import frappe

from compendium.install import DOCUMENTATION_ROUTE

# v16 serves the Desk at /desk; /app only redirects there.
OLD_DOCUMENTATION_ROUTE = "/app/docs"


def execute():
	navbar_settings = frappe.get_single("Navbar Settings")

	for item in navbar_settings.help_dropdown:
		if item.route == OLD_DOCUMENTATION_ROUTE:
			item.route = DOCUMENTATION_ROUTE
			navbar_settings.save()
			return
