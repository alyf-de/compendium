// Extend Custom breadcrumbs to support items[] (from frappe PR #41458, adapted for v15)
(function () {
	if (!frappe.breadcrumbs || frappe.breadcrumbs.__compendium_items_patch) {
		return;
	}
	frappe.breadcrumbs.__compendium_items_patch = true;
	const original = frappe.breadcrumbs.set_custom_breadcrumbs.bind(frappe.breadcrumbs);
	frappe.breadcrumbs.set_custom_breadcrumbs = function (breadcrumbs) {
		if (breadcrumbs.items?.length) {
			breadcrumbs.items.forEach((item, index) => {
				this.append_breadcrumb_element(item.route, item.label);
				if (item.disabled || index === breadcrumbs.items.length - 1) {
					this.$breadcrumbs.find("li").last().addClass("disabled");
				}
			});
			return;
		}
		original(breadcrumbs);
	};
})();
