import frappe

DOCUMENTATION_ROUTE = "/app/docs"
COMPENDIUM_LABEL = "Compendium"


def after_install():
	add_documentation_help_item()


def add_documentation_help_item():
	navbar_settings = frappe.get_single("Navbar Settings")

	for item in navbar_settings.help_dropdown:
		if item.route == DOCUMENTATION_ROUTE:
			return

	navbar_settings.append(
		"help_dropdown",
		{
			"item_label": COMPENDIUM_LABEL,
			"item_type": "Route",
			"route": DOCUMENTATION_ROUTE,
			"is_standard": 1,
		},
	)
	navbar_settings.save()
