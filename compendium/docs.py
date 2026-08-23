# Copyright (c) 2026, ALYF GmbH and Contributors
# License: MIT. See LICENSE

import importlib.util
import os
import re
from collections import Counter
from urllib.parse import quote, urlencode

import frappe
from frappe import _
from frappe.translate import get_parent_language
from frappe.utils import cint, get_url, has_common, sanitize_html
from frappe.utils.change_log import parse_github_url
from frappe.website.utils import extract_title, get_frontmatter

from compendium.permissions import CONTRIBUTOR_ROLE

DOCS_FOLDER = "docs"
DEFAULT_LANG = "en"
DEFAULT_ROLE = "Desk User"
ALLOWED_FRONTMATTER_KEYS = ("title", "order", "roles")
IMAGE_SRC_PATTERN = re.compile(r'(<img[^>]+src=["\'])([^"\']+)(["\'])', re.IGNORECASE)
GITHUB_ALERT_MARKER = re.compile(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\][ \t]*", re.IGNORECASE)
GITHUB_ALERTS = {
	"NOTE": ("Note", "info"),
	"TIP": ("Tip", "light-bulb"),
	"IMPORTANT": ("Important", "megaphone"),
	"WARNING": ("Warning", "alert"),
	"CAUTION": ("Caution", "stop"),
}


@frappe.whitelist()
def get_tree(locale: str | None = None):
	"""Return the documentation navigation tree for pages the current user may access."""
	return build_navigation_tree(locale)


@frappe.whitelist()
def get_page(path: str = "", locale: str | None = None):
	"""Return rendered HTML and metadata for a documentation page at the given logical path."""
	locale = normalize_locale(locale)
	page = get_page_record(normalize_path(path), locale=locale, check_permission=True)
	return build_page_payload(page, locale)


@frappe.whitelist()
def get_view(path: str = "", locale: str | None = None, resolve_first: int | bool = 0):
	"""Return everything the docs browser needs for one screen.

	Always includes the navigation tree. When the requested page is missing or not
	permitted, `page` is None and `exc_type` explains why — the request still
	succeeds so the client can render the sidebar. Pass `resolve_first` when the
	route has a locale but no path; the first accessible page is selected.
	"""
	locale = normalize_locale(locale)
	pages = discover_pages(locale)
	tree = build_navigation_tree(locale)
	first_path = get_first_page_path(pages)

	if cint(resolve_first):
		path = first_path
	else:
		path = normalize_path(path)

	if path is None:
		return {
			"tree": tree,
			"page": None,
			"variants": [],
			"path": None,
			"first_path": None,
			"exc_type": None,
		}

	page_record = pages.get(path)
	if not page_record:
		return {
			"tree": tree,
			"page": None,
			"variants": [],
			"path": path,
			"first_path": first_path,
			"exc_type": "DoesNotExistError",
		}

	if not is_permitted(page_record):
		return {
			"tree": tree,
			"page": None,
			"variants": [],
			"path": path,
			"first_path": first_path,
			"exc_type": "PermissionError",
		}

	return {
		"tree": tree,
		"page": build_page_payload(page_record, locale),
		"variants": get_page_variants(path),
		"path": path,
		"first_path": first_path,
		"exc_type": None,
	}


def build_page_payload(page, locale):
	content = render_page_content(page.body, page.path, locale)
	user_roles = set(get_user_roles())
	matching_roles = [role for role in page.roles if role in user_roles]
	return {
		"path": page.path,
		"title": page.title,
		"locale": locale,
		"language": page.language,
		"language_label": get_locale_label(page.language),
		"is_fallback": is_language_fallback(page.language, locale),
		"content": content,
		"toc_html": render_toc(page.body),
		"roles": [_(role) for role in matching_roles],
		"edit_url": get_edit_url(page),
	}


@frappe.whitelist()
def get_first_page(locale: str | None = None):
	"""Return the logical path of the first accessible documentation page."""
	locale = normalize_locale(locale)
	pages = discover_pages(locale)
	return get_first_page_path(pages)


@frappe.whitelist()
def resolve_locale(path: str = ""):
	"""Resolve a stable locale and path for a language-neutral docs route."""
	path = normalize_path(path)
	raw_pages = discover_raw_pages()
	locale = get_view_locale(raw_pages)

	if path:
		return {"locale": locale, "path": path}

	pages = compose_pages(raw_pages, locale)
	first_path = get_first_page_path(pages)
	return {"locale": locale, "path": first_path if first_path is not None else ""}


def get_view_locale(raw_pages):
	"""The locale a reader browses in: their own language, or the closest documented one.

	Composition falls back per page, so this only decides which locale the route carries.
	It has to be a documented one — the client recognises a route segment as a locale by
	matching it against `get_locales()`, and an unknown segment would be read as a path.
	"""
	locale = normalize_locale(frappe.local.lang or DEFAULT_LANG)
	documented = {language for language, _path in raw_pages}
	if not documented or locale in documented:
		return locale

	for language in get_language_chain(locale):
		if language in documented:
			return language

	# Nothing in the reader's chain is documented: use the doc set's main language.
	counts = Counter(language for language, _path in raw_pages)
	return min(documented, key=lambda language: (-counts[language], language))


def is_language_fallback(language, locale):
	"""True when a page is shown in a language the reader did not ask for."""
	return language != locale and language != get_parent_language(locale)


@frappe.whitelist()
def get_locales():
	"""Return locales that have documentation, with display labels."""
	return get_documented_locale_infos()


@frappe.whitelist()
def get_page_variants(path: str = ""):
	"""Return the locales this page can be viewed in, and the language each one renders."""
	path = normalize_path(path)
	raw_pages = discover_raw_pages()
	variants = []

	for locale_info in get_documented_locale_infos(raw_pages):
		locale = locale_info["locale"]
		page = compose_pages(raw_pages, locale).get(path)
		if not page or not is_permitted(page):
			continue

		variants.append(
			{
				"locale": locale,
				"label": locale_info["label"],
				"title": page.title,
				"language": page.language,
			}
		)

	return variants


@frappe.whitelist()
def get_asset(page_path: str, asset_path: str, locale: str | None = None):
	"""Serve a documentation asset after verifying access to the referring page."""
	locale = normalize_locale(locale)
	page = get_page_record(normalize_path(page_path), locale=locale, check_permission=True)
	asset_file = resolve_asset_path(page, asset_path)

	with open(asset_file, "rb") as f:
		content = f.read()

	filename = os.path.basename(asset_file)
	# as_raw (type "download") sets the MIME type from the filename. type "binary"
	# is always application/octet-stream, which browsers refuse to render as SVG.
	frappe.response["type"] = "download"
	frappe.response["filename"] = filename
	frappe.response["filecontent"] = content
	frappe.response["display_content_as"] = "inline"


def get_documented_locale_infos(raw_pages=None):
	raw_pages = raw_pages or discover_raw_pages()
	locales = sorted({language for language, path in raw_pages})
	return [{"locale": locale, "label": get_locale_label(locale)} for locale in locales]


@frappe.request_cache
def get_language_labels():
	return {
		row.name: row.language_name or row.name
		for row in frappe.get_all("Language", fields=["name", "language_name"])
	}


def get_locale_label(locale):
	return get_language_labels().get(locale, locale)


def discover_pages(locale=None):
	"""Discover and compose documentation pages for the requested locale."""
	locale = normalize_locale(locale or frappe.local.lang or DEFAULT_LANG)
	return compose_pages(discover_raw_pages(), locale)


def get_installed_apps():
	"""Installed apps for docs discovery. Separated so tests can patch without touching global frappe."""
	return frappe.get_installed_apps()


def get_app_path(app):
	"""App path for docs discovery. Separated so tests can patch without touching global frappe."""
	return frappe.get_app_path(app)


@frappe.request_cache
def discover_raw_pages():
	"""Discover documentation pages from all installed apps, grouped by language."""
	pages = {}

	for app_index, app in enumerate(get_installed_apps()):
		app_path = get_app_path(app)
		docs_root = os.path.join(app_path, DOCS_FOLDER)
		if not os.path.isdir(docs_root):
			continue

		for basepath, _folders, files in os.walk(docs_root):
			for fname in files:
				if not fname.endswith(".md"):
					continue

				filepath = os.path.join(basepath, fname)
				language, logical_path = parse_docs_path(docs_root, basepath, fname)
				if not language:
					continue

				page = build_page_record(filepath, app, docs_root, app_path, language, logical_path)
				page.app_index = app_index
				pages[(language, logical_path)] = page

	return pages


def compose_pages(raw_pages, locale):
	"""Compose the final page map for the requested locale.

	Every documented path is composed for every locale. The body comes from the best
	language available for that path, the metadata (order, roles) from the path's
	canonical page — so a page that exists in one language only stays reachable and
	keeps its place in the tree for every reader.
	"""
	canonical_languages = get_canonical_languages(raw_pages)
	composed = {}

	for path, variants in group_variants_by_path(raw_pages).items():
		canonical = pick_canonical_page(variants, canonical_languages)
		page = select_page_for_locale(variants, locale, canonical)
		composed[path] = page if page is canonical else merge_translated_page(canonical, page)

	return composed


def group_variants_by_path(raw_pages):
	"""Regroup discovery output into {logical path: {language: page}}."""
	variants_by_path = {}
	for (language, path), page in raw_pages.items():
		variants_by_path.setdefault(path, {})[language] = page
	return variants_by_path


def select_page_for_locale(variants, locale, canonical):
	"""First variant along the locale's language chain, else the canonical page.

	A variant that is not the canonical page is a translation of it, and only counts
	when it ships with the app owning the canonical page or a later one — otherwise a
	stale translation would override newer canonical content.
	"""
	for language in get_language_chain(locale):
		page = variants.get(language)
		if page and (page is canonical or page.app_index >= canonical.app_index):
			return page

	return canonical


def pick_canonical_page(variants, canonical_languages):
	"""The variant that owns a path's metadata.

	English wherever English exists, so apps that document in English are unaffected.
	For a path with no English variant it is the owning app's page in that app's
	canonical language — never another app's, or the owning app's content would be
	served under a foreign app's roles.
	"""
	english_page = variants.get(DEFAULT_LANG)
	if english_page:
		return english_page

	owner = max(variants.values(), key=lambda page: page.app_index)
	language = canonical_languages.get(owner.app, owner.language)
	canonical = variants.get(language)
	return canonical if canonical and canonical.app == owner.app else owner


def get_canonical_languages(raw_pages):
	"""Canonical language per app: the one its docs are authored in.

	English when the app ships any, otherwise the app's only language — so a single
	language app needs no configuration. An app documenting in several languages with
	no English can declare `docs_canonical_language` in hooks.py; without it the
	language carrying the most pages wins.
	"""
	page_counts = {}
	for (language, _path), page in raw_pages.items():
		page_counts.setdefault(page.app, Counter())[language] += 1

	canonical_languages = {}
	for app, languages in page_counts.items():
		if DEFAULT_LANG in languages:
			canonical_languages[app] = DEFAULT_LANG
		elif len(languages) == 1:
			canonical_languages[app] = next(iter(languages))
		else:
			declared = get_declared_canonical_language(app)
			canonical_languages[app] = (
				declared
				if declared in languages
				else min(languages, key=lambda language: (-languages[language], language))
			)

	return canonical_languages


def get_declared_canonical_language(app):
	try:
		# frappe.get_hooks() prints and raises for an app it cannot import
		if not importlib.util.find_spec(f"{app}.hooks"):
			return None
	except (ImportError, ValueError):
		return None

	declared = frappe.get_hooks("docs_canonical_language", app_name=app)
	return declared[-1] if declared else None


def get_language_chain(locale):
	lang = normalize_locale(locale)
	chain = [lang]
	parent = get_parent_language(lang)
	if parent and parent not in chain:
		chain.append(parent)
	if DEFAULT_LANG not in chain:
		chain.append(DEFAULT_LANG)
	return chain


def get_first_page_path(pages):
	permitted = sorted(
		(page for page in pages.values() if is_permitted(page)),
		key=lambda page: (page.order, page.title.lower(), page.path),
	)
	if not permitted:
		return None
	return permitted[0].path


def merge_translated_page(canonical, localized):
	return frappe._dict(
		{
			"path": canonical.path,
			"title": localized.title,
			"order": canonical.order,
			"roles": canonical.roles,
			"body": localized.body,
			"app": localized.app,
			"app_index": localized.app_index,
			"language": localized.language,
			"filepath": localized.filepath,
			"basepath": localized.basepath,
			"docs_root": localized.docs_root,
			"app_path": localized.app_path,
		}
	)


def parse_docs_path(docs_root, basepath, filename):
	page_name, _ext = os.path.splitext(filename)
	relative_dir = os.path.relpath(basepath, docs_root)
	dir_parts = [] if relative_dir == "." else relative_dir.split(os.sep)

	if not dir_parts or not is_language_code(dir_parts[0]):
		return None, None

	language = dir_parts[0]
	content_parts = dir_parts[1:]

	if page_name == "index":
		logical_path = "" if not content_parts else "/".join(content_parts)
	else:
		logical_path = "/".join([*content_parts, page_name]) if content_parts else page_name

	return language, logical_path


@frappe.request_cache
def get_language_codes():
	return set(frappe.get_all("Language", pluck="name"))


def is_language_code(segment):
	return segment in get_language_codes()


def normalize_locale(locale):
	locale = (locale or DEFAULT_LANG).strip()
	if is_language_code(locale):
		return locale

	parent = get_parent_language(locale)
	if parent and is_language_code(parent):
		return locale

	frappe.throw(_("Invalid documentation locale"), frappe.ValidationError)


def build_page_record(filepath, app, docs_root, app_path, language, logical_path):
	with open(filepath, encoding="utf-8") as f:
		source = f.read()

	res = get_frontmatter(source)
	# get_frontmatter returns an empty body when there is no --- frontmatter block
	attributes = parse_frontmatter_attributes(res["attributes"])
	body = res["body"] if res["attributes"] else source
	page_name = os.path.splitext(os.path.basename(filepath))[0]
	title = attributes.get("title") or extract_title(body, logical_path or page_name)

	return frappe._dict(
		{
			"path": logical_path,
			"title": title,
			"order": cint(attributes.get("order", 0)),
			"roles": parse_roles(attributes.get("roles")),
			"body": body,
			"language": language,
			"app": app,
			"filepath": filepath,
			"basepath": os.path.dirname(filepath),
			"docs_root": docs_root,
			"app_path": app_path,
		}
	)


def parse_frontmatter_attributes(attributes):
	if not attributes or not isinstance(attributes, dict):
		return {}

	return {key: attributes[key] for key in ALLOWED_FRONTMATTER_KEYS if key in attributes}


def parse_roles(roles):
	if roles is None:
		return [DEFAULT_ROLE]

	if isinstance(roles, str):
		return [role.strip() for role in roles.split(",") if role.strip()]

	if isinstance(roles, list):
		return [role for role in roles if role]

	return [DEFAULT_ROLE]


def normalize_path(path):
	if not path:
		return ""

	normalized = os.path.normpath(path.strip("/"))
	if normalized in (".", ""):
		return ""

	if normalized.startswith("..") or "/.." in normalized:
		frappe.throw(_("Invalid documentation path"), frappe.ValidationError)

	return normalized.replace(os.sep, "/")


def get_page_record(path, locale=None, check_permission=False):
	locale = normalize_locale(locale or DEFAULT_LANG)
	page = compose_pages(discover_raw_pages(), locale).get(path)

	if not page:
		frappe.throw(_("Documentation page not found"), frappe.DoesNotExistError)

	if check_permission and not is_permitted(page):
		raise frappe.PermissionError(_("No read permission for documentation page {0}").format(page.title))

	return page


def get_user_roles():
	"""Current user roles for docs access. Separated so tests can patch without touching global frappe."""
	return frappe.get_roles()


def is_permitted(page):
	if frappe.session.user == "Administrator":
		return True

	return has_common(get_user_roles(), page.roles)


def can_edit_on_github():
	"""Only contributors see the Edit on GitHub control."""
	if frappe.session.user == "Administrator":
		return True

	return CONTRIBUTOR_ROLE in get_user_roles()


def get_edit_url(page):
	"""GitHub edit URL for the Markdown file currently rendered, or None."""
	if not can_edit_on_github():
		return None

	repository = get_app_repository_url(page.app)
	if not repository:
		return None

	try:
		owner, repo = parse_github_url(repository)
	except ValueError:
		return None

	if not owner or not repo:
		return None

	branch = get_app_docs_branch(page.app)
	if not branch:
		return None

	relative_path = get_repo_relative_path(page)
	if not relative_path:
		return None

	# Branch names may contain slashes (e.g. feat/foo); encode so GitHub can
	# tell the ref apart from the file path.
	return f"https://github.com/{owner}/{repo}/edit/{quote(branch, safe='')}/{relative_path}"


@frappe.request_cache
def get_app_pyproject(app):
	"""Parsed pyproject.toml for an installed app, or an empty dict."""
	from tomli import load

	pyproject_path = os.path.join(os.path.dirname(get_app_path(app)), "pyproject.toml")
	if not os.path.isfile(pyproject_path):
		return {}

	with open(pyproject_path, "rb") as f:
		return load(f)


def get_app_repository_url(app):
	"""Repository URL from the app's pyproject.toml `[project.urls]` Repository key."""
	url = (get_app_pyproject(app).get("project") or {}).get("urls", {}).get("Repository")
	return url.rstrip("/") if url else None


def get_app_docs_branch(app):
	"""GitHub branch for Edit on GitHub, from `[tool.compendium] docs_branch`."""
	return ((get_app_pyproject(app).get("tool") or {}).get("compendium") or {}).get("docs_branch") or ""


def get_repo_relative_path(page):
	"""Path of the page's Markdown file relative to the app repository root."""
	repo_root = os.path.realpath(os.path.dirname(page.app_path))
	filepath = os.path.realpath(page.filepath)
	try:
		relative = os.path.relpath(filepath, repo_root)
	except ValueError:
		return None

	if relative.startswith(".."):
		return None

	return relative.replace(os.sep, "/")


def build_navigation_tree(locale=None):
	locale = normalize_locale(locale or frappe.local.lang or DEFAULT_LANG)
	permitted_pages = {path: page for path, page in discover_pages(locale).items() if is_permitted(page)}
	if not permitted_pages:
		return []

	paths = set(permitted_pages.keys())
	for path in permitted_pages:
		for prefix in get_path_prefixes(path):
			paths.add(prefix)

	nodes = {}
	for path in paths:
		page = permitted_pages.get(path)
		if page:
			nodes[path] = {
				"path": path,
				"title": page.title,
				"order": page.order,
				"has_page": True,
				"children": [],
			}
		else:
			nodes[path] = {
				"path": path,
				"title": title_from_path_segment(path.rsplit("/", 1)[-1]),
				"order": 0,
				"has_page": False,
				"children": [],
			}

	roots = []
	for path, node in nodes.items():
		parent_path = path.rsplit("/", 1)[0] if "/" in path else ""
		if parent_path and parent_path in nodes:
			nodes[parent_path]["children"].append(node)
		elif not parent_path:
			roots.append(node)

	sort_tree_nodes(roots)
	return roots


def get_path_prefixes(path):
	if not path:
		return []

	parts = path.split("/")
	return ["/".join(parts[:index]) for index in range(1, len(parts))]


def title_from_path_segment(segment):
	return segment.replace("_", " ").replace("-", " ").title()


def sort_tree_nodes(nodes):
	nodes.sort(key=lambda node: (node["order"], node["title"].lower(), node["path"]))
	for node in nodes:
		sort_tree_nodes(node["children"])


def render_page_content(body, page_path="", locale=None):
	html = frappe.utils.md_to_html(body or "")
	content = apply_github_alerts(str(html))
	content = sanitize_html(content, linkify=True)
	return rewrite_asset_urls(content, page_path, locale)


def apply_github_alerts(html):
	"""Turn GitHub alert markers into a titled, typed blockquote."""
	from bs4 import BeautifulSoup, NavigableString

	if not html or "[!" not in html:
		return html

	soup = BeautifulSoup(html, "html.parser")
	for blockquote in soup.find_all("blockquote"):
		paragraph = next((child for child in blockquote.children if child.name), None)
		if not paragraph or paragraph.name != "p":
			continue

		text_node = next(
			(
				child
				for child in paragraph.children
				if not isinstance(child, NavigableString) or str(child).strip()
			),
			None,
		)
		if not isinstance(text_node, NavigableString):
			continue

		leading = str(text_node).lstrip()
		match = GITHUB_ALERT_MARKER.match(leading)
		if not match:
			continue

		alert_type = match.group(1).upper()
		remainder = leading[match.end() :].lstrip()
		blockquote["class"] = [
			*(blockquote.get("class") or []),
			"docs-alert",
			f"docs-alert-{alert_type.lower()}",
		]
		title = build_alert_title(soup, alert_type)

		if remainder:
			text_node.replace_with(remainder)
			paragraph.insert_before(title)
		else:
			text_node.extract()
			if paragraph.get_text(strip=True) or paragraph.find(True):
				paragraph.insert_before(title)
			else:
				paragraph.replace_with(title)

	return str(soup)


def build_alert_title(soup, alert_type):
	label, icon = GITHUB_ALERTS[alert_type]
	title = soup.new_tag("p", attrs={"class": "docs-alert-title"})
	icon_tag = soup.new_tag("i", attrs={"class": f"octicon octicon-{icon}"})
	title.append(icon_tag)
	title.append(label)
	return title


def rewrite_asset_urls(html, page_path, locale=None):
	def replace(match):
		prefix, src, suffix = match.groups()
		if src.startswith(("http://", "https://", "data:", "/")):
			return match.group(0)

		return f"{prefix}{get_asset_url(page_path, src, locale)}{suffix}"

	return IMAGE_SRC_PATTERN.sub(replace, html or "")


def get_asset_url(page_path, asset_path, locale=None):
	query = urlencode(
		{
			"page_path": page_path,
			"asset_path": asset_path,
			"locale": normalize_locale(locale),
		}
	)
	return get_url(f"/api/method/compendium.docs.get_asset?{query}")


def render_toc(body):
	html = frappe.utils.md_to_html(body or "")
	if not html or not getattr(html, "toc_html", None):
		return ""

	return frappe.utils.sanitize_html(html.toc_html, linkify=True)


def resolve_asset_path(page, asset_path):
	normalized_asset_path = normalize_asset_path(asset_path)
	asset_file = os.path.realpath(os.path.join(page.basepath, normalized_asset_path))
	docs_root = os.path.realpath(page.docs_root)

	if not asset_file.startswith(docs_root + os.sep):
		frappe.throw(_("Invalid asset path"), frappe.ValidationError)

	if not os.path.isfile(asset_file):
		frappe.throw(_("Documentation asset not found"), frappe.DoesNotExistError)

	return asset_file


def normalize_asset_path(asset_path):
	if not asset_path:
		frappe.throw(_("Invalid asset path"), frappe.ValidationError)

	normalized = os.path.normpath(asset_path.strip("/\\"))
	if normalized in (".", "") or normalized.startswith("..") or "/.." in normalized.replace("\\", "/"):
		frappe.throw(_("Invalid asset path"), frappe.ValidationError)

	return normalized
