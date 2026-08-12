import frappe

from compendium.permissions import CONTRIBUTOR_ROLE

DOCUMENTATION_ROUTE = "/app/docs"
COMPENDIUM_LABEL = "Compendium"


def after_install():
	add_documentation_help_item()
	ensure_contributor_role()


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


def ensure_contributor_role():
	if frappe.db.exists("Role", CONTRIBUTOR_ROLE):
		return

	frappe.get_doc({"doctype": "Role", "role_name": CONTRIBUTOR_ROLE, "desk_access": 1}).insert(
		ignore_permissions=True
	)
