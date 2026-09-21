from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from compendium.install import DOCUMENTATION_ROUTE
from compendium.patches.update_documentation_route import OLD_DOCUMENTATION_ROUTE, execute


class TestUpdateDocumentationRoute(TestCase):
	@patch("compendium.patches.update_documentation_route.frappe.get_single")
	def test_updates_only_old_documentation_route(self, get_single):
		documentation_item = SimpleNamespace(route=OLD_DOCUMENTATION_ROUTE, item_label="Compendium")
		other_item = SimpleNamespace(route="/app/other", item_label="Other")
		navbar_settings = Mock(help_dropdown=[documentation_item, other_item])
		get_single.return_value = navbar_settings

		execute()

		self.assertEqual(documentation_item.route, DOCUMENTATION_ROUTE)
		self.assertEqual(other_item.route, "/app/other")
		navbar_settings.save.assert_called_once_with()
