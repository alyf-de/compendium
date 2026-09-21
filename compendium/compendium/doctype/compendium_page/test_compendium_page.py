# Copyright (c) 2026, ALYF GmbH and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from compendium.docs import discover_pages, get_asset, get_page, get_view
from compendium.search import awesomebar_results
from compendium.tests.test_docs import DocsTestEnvironment


class TestCompendiumPage(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.local.lang = "en"
		self.next_request()

	def tearDown(self):
		frappe.db.rollback()
		frappe.set_user("Administrator")
		frappe.local.lang = "en"

	def next_request(self):
		if hasattr(frappe.local, "request_cache"):
			frappe.local.request_cache.clear()

	def make_page(self, title, content="", **kwargs):
		roles = kwargs.pop("roles", [])
		doc = frappe.get_doc(
			{
				"doctype": "Compendium Page",
				"title": title,
				"language": "en",
				"content": content,
				"roles": [{"role": role} for role in roles],
				**kwargs,
			}
		).insert()
		self.next_request()
		return doc

	def test_path_is_slugged_from_title_and_normalized(self):
		self.assertEqual(self.make_page("Getting Started — Übersicht!").path, "getting-started-übersicht")
		self.assertEqual(self.make_page("Nested", path="/guides//nested/").path, "guides/nested")

		with self.assertRaises(frappe.ValidationError):
			self.make_page("Escape", path="../secrets")
		with self.assertRaises(frappe.ValidationError):
			self.make_page("!!!")

	def test_markdown_is_stored_verbatim_and_sanitized_on_render(self):
		with DocsTestEnvironment({}, db_pages=True):
			doc = self.make_page("Quote", "> [!NOTE]\n> Quoted\n\n<script>alert(1)</script>")
			content = get_page("quote", locale="en")["content"]

		self.assertTrue(doc.content.startswith("> [!NOTE]"))
		self.assertIn("docs-alert-note", content)
		self.assertNotIn("<script>", content)

	def test_path_is_unique_per_language(self):
		self.make_page("Wiki Unique")
		self.make_page("Wiki Unique", language="de")
		with self.assertRaises(frappe.DuplicateEntryError):
			self.make_page("Wiki Unique")

	def test_page_is_added_on_top_of_app_docs(self):
		with DocsTestEnvironment({"en/shipped.md": "# Shipped"}, db_pages=True):
			self.make_page("Site Wiki", "Our own notes")
			pages = discover_pages("en")

		self.assertIn("shipped", pages)
		self.assertEqual(pages["site-wiki"].body, "Our own notes")
		self.assertEqual(pages["site-wiki"].roles, ["Desk User"])

	def test_page_overrides_app_page_at_same_path(self):
		with DocsTestEnvironment({"en/shared.md": "---\ntitle: Shipped\n---\nWrong for us"}, db_pages=True):
			self.make_page("Corrected", "Right for us", path="shared", roles=["System Manager"])
			page = discover_pages("en")["shared"]

		self.assertEqual(page.title, "Corrected")
		self.assertEqual(page.roles, ["System Manager"])

	def test_unpublished_page_neither_shows_nor_hides(self):
		with DocsTestEnvironment({"en/shared.md": "---\ntitle: Shipped\n---\nBody"}, db_pages=True):
			self.make_page("Draft Override", path="shared", published=0)
			self.make_page("Draft Page", published=0)
			pages = discover_pages("en")

		self.assertEqual(pages["shared"].title, "Shipped")
		self.assertNotIn("draft-page", pages)

	def test_translation_takes_roles_of_canonical_page(self):
		files = {"en/guides/setup.md": "---\ntitle: Setup\nroles: System Manager\n---\nEnglish"}
		with DocsTestEnvironment(files, db_pages=True):
			self.make_page("Einrichtung", "Deutsch", path="guides/setup", language="de", roles=["Desk User"])
			page = discover_pages("de")["guides/setup"]

		self.assertEqual(page.body, "Deutsch")
		self.assertEqual(page.roles, ["System Manager"])

	def test_edit_route_replaces_github_link(self):
		with DocsTestEnvironment(
			{}, repository="https://github.com/alyf-de/compendium", docs_branch="main", db_pages=True
		):
			doc = self.make_page("Editable")
			payload = get_page("editable", locale="en")

		self.assertIsNone(payload["edit_url"])
		self.assertEqual(payload["edit_route"], f"/app/compendium-page/{doc.name}")

	def test_serves_only_attached_private_files(self):
		with DocsTestEnvironment({}, db_pages=True):
			doc = self.make_page("With Image")
			attached = self.make_private_file("attached.png", b"attached", doc.name)
			elsewhere = self.make_private_file("elsewhere.png", b"elsewhere")
			doc.content = f"![Image]({attached.file_url})\n\n[Other]({elsewhere.file_url})"
			doc.save()
			self.next_request()

			content = get_view("with-image", locale="en")["page"]["content"]
			self.assertNotIn('"/private/files/', content)
			self.assertIn("compendium.docs.get_asset", content)

			get_asset("with-image", attached.file_url, locale="en")
			self.assertEqual(frappe.response["filecontent"], b"attached")

			with self.assertRaises(frappe.DoesNotExistError):
				get_asset("with-image", elsewhere.file_url, locale="en")

	def test_private_files_require_page_access(self):
		with DocsTestEnvironment({}, db_pages=True):
			doc = self.make_page("Restricted Image", roles=["System Manager"])
			attached = self.make_private_file("restricted.png", b"secret", doc.name)

			frappe.set_user("test@example.com")
			with patch("compendium.docs.get_user_roles", return_value=["Desk User"]):
				with self.assertRaises(frappe.PermissionError):
					get_asset("restricted-image", attached.file_url, locale="en")

	def test_search_sees_saved_and_deleted_pages(self):
		with DocsTestEnvironment({}, db_pages=True):
			self.assertEqual(awesomebar_results("zymurgy"), [])

			doc = self.make_page("Brewing", "All about zymurgy.")
			self.assertEqual([item["label"] for item in awesomebar_results("zymurgy")], ["Brewing"])

			doc.delete()
			self.next_request()
			self.assertEqual(awesomebar_results("zymurgy"), [])

	def make_private_file(self, file_name, content, attached_to_name=None):
		return frappe.get_doc(
			{
				"doctype": "File",
				"file_name": file_name,
				"content": content,
				"is_private": 1,
				"attached_to_doctype": "Compendium Page" if attached_to_name else None,
				"attached_to_name": attached_to_name,
			}
		).insert()
