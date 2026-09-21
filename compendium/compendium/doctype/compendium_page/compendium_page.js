// Copyright (c) 2026, ALYF GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on("Compendium Page", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.language) {
			frm.set_value("language", frappe.boot.lang);
		}
	},

	refresh(frm) {
		// the Markdown Editor attaches dropped images only to a saved page
		frm.set_intro(frm.is_new() ? __("Save the page before adding images.") : "");

		if (!frm.is_new() && frm.doc.published) {
			frm.add_custom_button(__("View"), () => {
				frappe.set_route(["docs", frm.doc.language, ...frm.doc.path.split("/")]);
			});
		}
	},

	title(frm) {
		if (!frm.doc.path) {
			// same slug as slugify() in compendium_page.py
			const slug = (frm.doc.title || "")
				.toLowerCase()
				.replace(/[^\p{L}\p{N}]+/gu, "-")
				.replace(/^-+|-+$/g, "");
			frm.set_value("path", slug);
		}
	},
});
