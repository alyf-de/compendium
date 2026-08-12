import frappe

from compendium.install import COMPENDIUM_LABEL, DOCUMENTATION_ROUTE


def execute():
	navbar_settings = frappe.get_single("Navbar Settings")

	for item in navbar_settings.help_dropdown:
		if item.route == DOCUMENTATION_ROUTE:
			item.item_label = COMPENDIUM_LABEL
			navbar_settings.save()
			return
