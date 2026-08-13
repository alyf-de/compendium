import frappe

CONTRIBUTOR_ROLE = "Compendium Contributor"


def has_app_permission():
	"""Show Compendium on the apps screen for Desk users."""
	if frappe.session.user == "Administrator":
		return True

	return "Desk User" in frappe.get_roles()
