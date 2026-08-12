frappe.provide("frappe.ui");

frappe.pages["docs"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Documentation"),
		single_column: false,
	});

	frappe.docs_browser = new frappe.ui.DocsBrowser({ page, wrapper });
};

frappe.pages["docs"].on_page_show = function () {
	frappe.docs_browser?.show();
};

frappe.ui.DocsBrowser = class DocsBrowser {
	constructor({ page, wrapper }) {
		this.page = page;
		this.wrapper = wrapper;
		this.tree_data = [];
		this.page_paths = new Set();
		this.expanded_paths = new Set();
		this.current_path = null;
		this.current_locale = frappe.boot.lang || "en";
		this.locales = [];
		this._view_seq = 0;
		this.layout_ready = Promise.resolve();
		this.setup_layout();
	}

	setup_layout() {
		// overlay-sidebar + hidden-xs/sm matches Desk list/form sidebars so the
		// page toggle opens a drawer on small screens and can hide on desktop.
		this.$sidebar = $(
			'<div class="docs-sidebar overlay-sidebar hidden-xs hidden-sm"></div>'
		).appendTo(this.page.sidebar);
		this.$tree = $('<div class="docs-tree"></div>').appendTo(this.$sidebar);
		this.$locale_picker = $(`
			<div class="docs-locale-picker">
				<label class="docs-locale-label" for="docs-locale-select">${__("Language")}</label>
				<select id="docs-locale-select" class="form-control docs-locale-select"></select>
			</div>
		`).appendTo(this.$sidebar);
		this.$locale_select = this.$locale_picker.find(".docs-locale-select");
		this.$locale_select.on("change", () => {
			this.switch_locale(this.$locale_select.val());
		});
		this.$content = $(frappe.render_template("docs")).appendTo(this.page.main);
		this.$reading = this.$content.find(".docs-reading-pane");
		this.$toc_pane = this.$content.find(".docs-toc-pane");
		this.$toc = this.$content.find(".docs-toc").attr("aria-label", __("On this page"));
		this.$state = this.$content.find(".docs-state");
		this.$state_message = this.$content.find(".docs-state-content");

		this.$tree.on("click", ".docs-tree-toggle", (event) => {
			event.preventDefault();
			event.stopPropagation();
			const path = $(event.currentTarget).closest(".docs-tree-item").attr("data-path");
			if (path === undefined) {
				return;
			}
			this.toggle_group(path);
		});

		this.$tree.on("click", ".docs-tree-node", (event) => {
			event.preventDefault();
			const $node = $(event.currentTarget);
			const path = $node.attr("data-path");
			if (path === undefined) {
				return;
			}
			if ($node.attr("data-has-page") !== "1") {
				this.toggle_group(path);
				return;
			}
			this.navigate_to(path);
		});

		// Desk treats href="#…" as v1 routes (/app/%23…). Keep in-page anchors local.
		this.$content.on("click", 'a[href^="#"]', (event) => {
			this.follow_in_page_anchor(event);
		});
	}

	show() {
		if (this._ignore_next_show) {
			this._ignore_next_show = false;
			return;
		}

		const route = frappe.get_route();
		this.ensure_locales().then(() => {
			const parsed = this.parse_route(route);
			if (!parsed.locale) {
				return this.resolve_and_redirect(parsed.path);
			}
			this.current_locale = parsed.locale;
			if (parsed.path === null) {
				return this.load_view("", true);
			}
			this.load_view(parsed.path);
		});
	}

	ensure_locales() {
		if (this.locales.length) {
			return Promise.resolve(this.locales);
		}
		return frappe.xcall("compendium.docs.get_locales").then((locales) => {
			this.locales = (locales || []).map((locale) =>
				typeof locale === "string" ? { locale, label: locale } : locale
			);
		});
	}

	get_locale_codes() {
		return this.locales.map((locale) => locale.locale);
	}

	render_locale_picker(variants = []) {
		const options = variants.length ? variants : this.locales;
		const current = this.$locale_select.val();

		this.$locale_picker.toggleClass("hide", options.length <= 1);
		this.$locale_select.empty();

		for (const option of options) {
			const locale = option.locale;
			const label = option.label || locale;
			this.$locale_select.append($("<option></option>").attr("value", locale).text(label));
		}

		if (options.some((option) => option.locale === this.current_locale)) {
			this.$locale_select.val(this.current_locale);
		} else if (current) {
			this.$locale_select.val(current);
		}
	}

	switch_locale(locale) {
		if (!locale || locale === this.current_locale) {
			return;
		}

		const path = this.current_path || "";
		const seq = ++this._view_seq;
		frappe.xcall("compendium.docs.get_view", { path, locale }).then((view) => {
			if (seq !== this._view_seq) {
				if (this.$locale_select.val() === locale) {
					this.$locale_select.val(this.current_locale);
				}
				return;
			}

			const target_path = view.page ? path : view.first_path;
			const route = ["docs", locale];
			if (target_path) {
				route.push(...target_path.split("/"));
			}

			if (view.page || target_path == null || target_path === path) {
				this.current_locale = locale;
				this._ignore_next_show = true;
				frappe.set_route(route);
				this.apply_view(view);
				return;
			}

			frappe.set_route(route);
		});
	}

	parse_route(route) {
		const segments = route.slice(1);
		if (segments.length && this.is_locale_segment(segments[0])) {
			return {
				locale: segments[0],
				path: segments.length > 1 ? segments.slice(1).join("/") : null,
			};
		}
		return {
			locale: null,
			path: segments.length ? segments.join("/") : null,
		};
	}

	is_locale_segment(segment) {
		const locale_codes = this.get_locale_codes();
		if (locale_codes.includes(segment)) {
			return true;
		}
		const parent = segment.split("-")[0];
		return parent !== segment && locale_codes.includes(parent);
	}

	resolve_and_redirect(path) {
		return frappe
			.xcall("compendium.docs.resolve_locale", { path: path || "" })
			.then((result) => {
				const route = ["docs", result.locale];
				if (result.path) {
					route.push(...result.path.split("/"));
				}
				frappe.set_route(route);
			});
	}

	apply_tree(tree) {
		this.tree_data = tree || [];
		this.page_paths = this.collect_page_paths(this.tree_data);
	}

	collect_page_paths(nodes) {
		const paths = new Set();
		for (const node of nodes) {
			if (node.has_page) {
				paths.add(node.path);
			}
			for (const child_path of this.collect_page_paths(node.children || [])) {
				paths.add(child_path);
			}
		}
		return paths;
	}

	render_tree() {
		this.$tree.empty();
		if (!this.tree_data.length) {
			return;
		}
		this.$tree.append(this.render_tree_nodes(this.tree_data));
	}

	render_tree_nodes(nodes) {
		const $list = $('<div class="docs-tree-list"></div>');
		for (const node of nodes) {
			const has_children = Boolean(node.children?.length);
			const collapsed = has_children && !this.expanded_paths.has(node.path);
			const escaped_path = frappe.utils.escape_html(node.path);
			const $item = $(
				`<div class="docs-tree-item" data-path="${escaped_path}" data-has-children="${
					has_children ? "1" : "0"
				}"></div>`
			);
			if (collapsed) {
				$item.addClass("collapsed");
			}

			const $row = $('<div class="docs-tree-row"></div>').appendTo($item);
			if (has_children) {
				$(
					`<button type="button" class="docs-tree-toggle" aria-expanded="${
						collapsed ? "false" : "true"
					}" aria-label="${frappe.utils.escape_html(
						__("Toggle {0}", [node.title])
					)}">${frappe.utils.icon("right", "xs")}</button>`
				).appendTo($row);
			} else {
				$('<span class="docs-tree-toggle-spacer" aria-hidden="true"></span>').appendTo(
					$row
				);
			}

			const classes = ["docs-tree-node"];
			if (node.path === this.current_path) {
				classes.push("active");
				$row.addClass("active");
			}
			if (!node.has_page) {
				classes.push("disabled");
			}
			$(
				`<a class="${classes.join(" ")}" data-path="${escaped_path}" data-has-page="${
					node.has_page ? "1" : "0"
				}" href="#">${frappe.utils.escape_html(node.title)}</a>`
			).appendTo($row);

			if (has_children) {
				$item.append(
					$('<div class="docs-tree-children"></div>').append(
						this.render_tree_nodes(node.children)
					)
				);
			}
			$list.append($item);
		}
		return $list;
	}

	toggle_group(path) {
		if (this.expanded_paths.has(path)) {
			this.expanded_paths.delete(path);
		} else {
			this.expanded_paths.add(path);
		}
		this.render_tree();
	}

	expand_ancestors(path) {
		if (path === null || path === undefined) {
			return;
		}
		const trail = this.find_path_trail(this.tree_data, path);
		if (!trail?.length) {
			return;
		}
		for (const node of trail) {
			this.expanded_paths.add(node.path);
		}
	}

	navigate_to(path, replace_route = false) {
		const route = ["docs", this.current_locale];
		if (path) {
			route.push(...path.split("/"));
		}
		if (replace_route) {
			frappe.set_route(route);
			return;
		}
		const current = frappe.get_route();
		const current_path = current.slice(2).join("/");
		if (current[1] !== this.current_locale || current_path !== path) {
			frappe.set_route(route);
			return;
		}
		this.load_view(path);
	}

	load_view(path, resolve_first = false) {
		this.show_loading();

		const seq = ++this._view_seq;
		return frappe.call({
			method: "compendium.docs.get_view",
			args: {
				path: path || "",
				locale: this.current_locale,
				resolve_first: resolve_first ? 1 : 0,
			},
			callback: (response) => {
				if (seq !== this._view_seq) {
					return;
				}
				if (response.exc_type && response.message == null) {
					this.show_error(response, path);
					return;
				}
				this.apply_view(response.message || {}, { resolve_first });
			},
		});
	}

	apply_view(view, { resolve_first = false } = {}) {
		this.apply_tree(view.tree);
		this.render_locale_picker(view.variants || []);

		if (resolve_first && view.path != null && view.path !== "") {
			this._ignore_next_show = true;
			this.navigate_to(view.path, true);
		}

		if (!view.page) {
			this.current_path = view.path;
			this.expand_ancestors(view.path);
			this.render_tree();
			if (!view.exc_type) {
				this.show_empty_state();
			} else {
				this.show_error({ exc_type: view.exc_type }, view.path);
			}
			return;
		}

		this.current_path = view.page.path;
		this.expand_ancestors(this.current_path);
		this.render_tree();
		this.show_page(view.page, view.variants);
	}

	show_loading() {
		this.$state.addClass("hide");
		this.$reading.removeClass("hide").addClass("docs-loading").html("");
		this.$toc_pane.addClass("hide");
		this.$content.removeClass("has-toc");
	}

	show_page(doc, variants) {
		this.$reading.removeClass("docs-loading hide");
		this.$state.addClass("hide");
		this.page.set_title(doc.title || __("Documentation"));
		this.$reading.html(doc.content || "");
		const toc_html = doc.toc_html || "";
		this.$toc.html(toc_html);
		this.$toc_pane.toggleClass("hide", !toc_html);
		this.$content.toggleClass("has-toc", Boolean(toc_html));
		this.render_fallback_notice(doc);
		this.render_roles(doc.roles);
		// Mermaid replaces fences with SVG asynchronously and shifts later headings;
		// fragment scrolls wait on layout_ready so they use the final layout.
		this.layout_ready = this.render_mermaid();
		this.scroll_to_heading();
		this.highlight_code();
		this.update_breadcrumbs(doc.path, doc.title);
		this.render_locale_picker(variants || []);
	}

	follow_in_page_anchor(event) {
		const href = event.currentTarget.getAttribute("href");
		if (!href || href === "#") {
			return;
		}

		event.preventDefault();
		event.stopPropagation();

		let id;
		try {
			id = decodeURIComponent(href.slice(1));
		} catch {
			return;
		}
		if (!id) {
			return;
		}

		// Do not set window.location.hash — Desk's hashchange handler treats it as a
		// v1 route and pushState("installieren") resolves relative to the current path.
		const url = `${window.location.pathname}${window.location.search}${href}`;
		if (
			`${window.location.pathname}${window.location.search}${window.location.hash}` !== url
		) {
			history.replaceState(null, "", url);
		}
		this.scroll_to_heading();
	}

	scroll_to_heading() {
		if (!window.location.hash.slice(1)) {
			return;
		}

		const path = this.current_path;
		this.layout_ready.finally(() => {
			if (this.current_path !== path) {
				return;
			}

			const hash = window.location.hash.slice(1);
			if (!hash) {
				return;
			}

			let id;
			try {
				id = decodeURIComponent(hash);
			} catch {
				return;
			}
			this.scroll_to_id(id);
		});
	}

	scroll_to_id(id) {
		const heading = document.getElementById(id);
		if (!heading || !this.$reading.has(heading).length) {
			return false;
		}
		heading.scrollIntoView();
		return true;
	}

	render_fallback_notice(doc) {
		if (!doc.is_fallback) {
			return;
		}

		const label = frappe.utils.escape_html(doc.language_label || doc.language);
		$(
			`<div class="docs-fallback-notice">${__("This page is only available in {0}.", [
				label,
			])}</div>`
		).prependTo(this.$reading);
	}

	render_roles(roles) {
		if (!roles?.length) {
			return;
		}

		const labels = roles.map((role) => frappe.utils.escape_html(role)).join(", ");
		const message =
			roles.length === 1
				? __("You can see this page because you have the role {0}.", [labels])
				: __("You can see this page because you have the roles {0}.", [labels]);
		this.$reading.append(`<footer class="docs-page-roles">${message}</footer>`);
	}

	render_mermaid() {
		const $blocks = this.$reading.find("pre code.language-mermaid, pre code.mermaid");
		if (!$blocks.length) {
			return Promise.resolve();
		}

		const nodes = [];
		$blocks.each((_, code) => {
			const $diagram = $('<div class="mermaid">').text(code.textContent || "");
			$(code).closest("pre").replaceWith($diagram);
			nodes.push($diagram.get(0));
		});

		return frappe
			.require("mermaid.bundle.js")
			.then(() =>
				this.ensure_mermaid().then(() =>
					compendium.mermaid.run({ nodes, suppressErrors: true })
				)
			);
	}

	highlight_code() {
		const blocks = this.$reading.find("pre code").not(".language-mermaid, .mermaid").get();
		if (!blocks.length) {
			return;
		}

		frappe
			.require(["syntax_highlighting.bundle.js", "/assets/frappe/css/hljs-night-owl.css"])
			.then(() => {
				for (const block of blocks) {
					if (block.isConnected) {
						compendium.hljs.highlightElement(block);
					}
				}
			});
	}

	ensure_mermaid() {
		if (compendium.mermaid_ready) {
			return Promise.resolve();
		}

		const theme =
			document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "default";
		compendium.mermaid.initialize({
			startOnLoad: false,
			securityLevel: "strict",
			theme,
		});
		compendium.mermaid_ready = true;
		return Promise.resolve();
	}

	show_empty_state() {
		this.current_path = null;
		this.render_tree();
		this.$reading.addClass("hide");
		this.$state.removeClass("hide");
		this.$state_message.text(__("No documentation is available for your account."));
		this.update_breadcrumbs();
		this.render_locale_picker([]);
	}

	show_error(response, path) {
		this.$reading.addClass("hide").removeClass("docs-loading");
		this.$state.removeClass("hide");
		this.update_breadcrumbs(path);

		const exc_type = response?.exc_type || response?.responseJSON?.exc_type;
		if (exc_type === "PermissionError") {
			this.$state_message.text(__("Sorry! You are not permitted to view this page."));
			return;
		}

		if (exc_type === "DoesNotExistError") {
			this.$state_message.text(__("Sorry! I could not find what you were looking for."));
			return;
		}

		this.$state_message.text(
			__("Unable to load documentation page {0}", [path || __("Home")])
		);
	}

	find_path_trail(nodes, path, trail = []) {
		for (const node of nodes) {
			const next_trail = [...trail, node];
			if (node.path === path) {
				return next_trail;
			}
			const child_trail = this.find_path_trail(node.children || [], path, next_trail);
			if (child_trail) {
				return child_trail;
			}
		}
		return null;
	}

	get_docs_route(path) {
		const route = `/app/docs/${this.current_locale}`;
		return path ? `${route}/${path}` : route;
	}

	update_breadcrumbs(path = null, title = null) {
		const items = [{ label: __("Documentation"), route: this.get_docs_route() }];

		if (path === null || path === undefined) {
			frappe.breadcrumbs.add({ type: "Custom", items });
			return;
		}

		const trail = this.find_path_trail(this.tree_data, path);
		if (trail?.length) {
			for (const node of trail) {
				items.push({
					label: node.title,
					route: node.has_page ? this.get_docs_route(node.path) : "",
					disabled: !node.has_page,
				});
			}
		} else {
			this.append_path_segment_breadcrumbs(items, path, title);
		}

		frappe.breadcrumbs.add({ type: "Custom", items });
	}

	append_path_segment_breadcrumbs(items, path, title) {
		const segments = path.split("/");
		let accumulated = "";

		for (let index = 0; index < segments.length; index++) {
			accumulated = accumulated ? `${accumulated}/${segments[index]}` : segments[index];
			const is_last = index === segments.length - 1;
			const node = this.find_tree_node(this.tree_data, accumulated);

			items.push({
				label:
					is_last && title
						? title
						: node?.title ||
						  frappe.utils.to_title_case(segments[index].replace(/-/g, " ")),
				route: !is_last && node?.has_page ? this.get_docs_route(accumulated) : "",
				disabled: is_last || !node?.has_page,
			});
		}
	}

	find_tree_node(nodes, path) {
		for (const node of nodes) {
			if (node.path === path) {
				return node;
			}
			const child = this.find_tree_node(node.children || [], path);
			if (child) {
				return child;
			}
		}
		return null;
	}
};
