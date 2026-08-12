from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from compendium.install import COMPENDIUM_LABEL, DOCUMENTATION_ROUTE
from compendium.patches.update_documentation_menu_label import execute


class TestUpdateDocumentationMenuLabel(TestCase):
	@patch("compendium.patches.update_documentation_menu_label.frappe.get_single")
	def test_updates_only_documentation_route(self, get_single):
		documentation_item = SimpleNamespace(route=DOCUMENTATION_ROUTE, item_label="Documentation")
		other_item = SimpleNamespace(route="/app/other", item_label="Documentation")
		navbar_settings = Mock(help_dropdown=[documentation_item, other_item])
		get_single.return_value = navbar_settings

		execute()

		self.assertEqual(documentation_item.item_label, COMPENDIUM_LABEL)
		self.assertEqual(other_item.item_label, "Documentation")
		navbar_settings.append.assert_not_called()
		navbar_settings.save.assert_called_once_with()
