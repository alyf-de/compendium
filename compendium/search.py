# Copyright (c) 2026, ALYF GmbH and Contributors
# License: MIT. See LICENSE

import os
import re
import sqlite3
import threading

import frappe
from frappe import _
from frappe.utils import escape_html

from compendium import docs
from compendium.docs import DEFAULT_LANG, DOCS_FOLDER, is_permitted, normalize_locale

RESULT_LIMIT = 20
TOKEN_PATTERN = re.compile(r"\w+")
SNIPPET_TOKENS = 12
ROLE_SEPARATOR = "\n"
# Columns are (path, title, roles, body); bm25 ranks a title hit above a body hit.
SEARCH_SQL = f"""
	SELECT path, title, roles, snippet(pages, 3, '', '', '…', {SNIPPET_TOKENS})
	FROM pages WHERE pages MATCH ? ORDER BY bm25(pages, 2.0, 10.0, 0.0, 1.0)
"""

# ponytail: one lock for all indexes; per-index locks if search ever gets hot
INDEX_LOCK = threading.Lock()
INDEXES = {}


def awesomebar_results(txt):
	"""Return matching docs pages for the Awesome Bar `awesomebar_search` hook."""
	match_query = build_match_query(txt)
	if not match_query:
		return []

	locale = normalize_locale(frappe.local.lang or DEFAULT_LANG)
	results = []

	for path, title, roles, snippet in search(locale, match_query):
		if not is_permitted(frappe._dict(roles=roles.split(ROLE_SEPARATOR))):
			continue

		route = f"/app/docs/{locale}/{path}" if path else f"/app/docs/{locale}"
		results.append(
			{
				"label": title,
				# the Awesome Bar renders the description as HTML
				"description": escape_html(snippet) or path or _("Documentation"),
				"route": route,
				"index": 50,
			}
		)
		if len(results) >= RESULT_LIMIT:
			break

	return results


def build_match_query(txt):
	"""Turn free text into an FTS5 MATCH expression: every word as a quoted prefix term.

	Quoting keeps words like `and` or `not` from being read as query operators.
	"""
	return " ".join(f'"{token}"*' for token in TOKEN_PATTERN.findall((txt or "").lower()))


def search(locale, match_query):
	with INDEX_LOCK:
		return get_index(locale).execute(SEARCH_SQL, (match_query,)).fetchall()


def get_index(locale):
	"""Full-content FTS5 index for one locale, kept in memory for the life of the worker.

	Rebuilt when a Markdown file appears, disappears or changes, so a docs deployment
	needs no restart and an author editing a page sees the change on the next search.
	Sites share a worker but not their installed apps, hence the site in the key.
	"""
	key = (frappe.local.site, locale)
	fingerprint = get_docs_fingerprint()
	cached = INDEXES.get(key)
	if cached and cached[0] == fingerprint:
		return cached[1]

	index = build_index(locale)
	INDEXES[key] = (fingerprint, index)
	return index


def build_index(locale):
	# the index outlives the request, so it outlives the thread that built it
	connection = sqlite3.connect(":memory:", check_same_thread=False)
	connection.execute(
		"CREATE VIRTUAL TABLE pages USING fts5"
		"(path, title, roles UNINDEXED, body, tokenize='unicode61 remove_diacritics 2')"
	)
	connection.executemany(
		"INSERT INTO pages (path, title, roles, body) VALUES (?, ?, ?, ?)",
		(
			(page.path, page.title, ROLE_SEPARATOR.join(page.roles), to_plain_text(page.body))
			for page in docs.discover_pages(locale).values()
		),
	)
	return connection


@frappe.request_cache
def get_docs_fingerprint():
	"""Staleness check for the index: every Markdown file with its mtime and size.

	Stat-only, so it costs a fraction of the reading and parsing an index build does.
	A file count and a newest mtime would be cheaper but would miss a deployment that
	restores the timestamps it found, leaving an edited page unsearchable until restart.
	"""
	stamps = []

	for app in docs.get_installed_apps():
		docs_root = os.path.join(docs.get_app_path(app), DOCS_FOLDER)
		for basepath, _folders, files in os.walk(docs_root):
			for fname in files:
				if not fname.endswith(".md"):
					continue

				filepath = os.path.join(basepath, fname)
				stat = os.stat(filepath)
				stamps.append((filepath, stat.st_mtime_ns, stat.st_size))

	return tuple(sorted(stamps))


def to_plain_text(markdown):
	"""The words of a page, without the markup around them.

	Markdown source makes both a poor preview and a poor index: a snippet cut out of it
	shows syntax mid-sentence, and link targets match queries the reader never sees.
	Image alt text is the exception among attributes — it is prose, so it is kept.
	"""
	from bs4 import BeautifulSoup

	soup = BeautifulSoup(frappe.utils.md_to_html(markdown or ""), "html.parser")
	for image in soup.find_all("img"):
		image.replace_with(image.get("alt") or "")

	return re.sub(r"\s+", " ", soup.get_text(" ")).strip()
