import os
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from compendium.search import awesomebar_results, get_index
from compendium.tests.test_docs import DocsTestEnvironment


class TestSearch(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.local.lang = "en"
		self.next_request()

	def next_request(self):
		"""Drop everything a single request caches, so the next call starts like a fresh one."""
		if hasattr(frappe.local, "request_cache"):
			frappe.local.request_cache.clear()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.local.lang = "en"

	def test_empty_query_returns_nothing(self):
		self.assertEqual(awesomebar_results(""), [])
		self.assertEqual(awesomebar_results("   "), [])
		self.assertEqual(awesomebar_results("!?-"), [])

	def test_matches_title_and_builds_docs_route(self):
		with DocsTestEnvironment(
			{
				"en/guides/setup.md": "---\ntitle: Setup Guide\n---\n# Setup\n\nInstall the app.",
				"en/other.md": "---\ntitle: Other\n---\n# Other",
			}
		):
			results = awesomebar_results("setup")

		self.assertEqual(len(results), 1)
		self.assertEqual(results[0]["label"], "Setup Guide")
		self.assertEqual(results[0]["route"], "/app/docs/en/guides/setup")
		self.assertEqual(results[0]["index"], 50)

	def test_matches_path(self):
		with DocsTestEnvironment(
			{
				"en/guides/setup.md": "---\ntitle: Setup Guide\n---\n# Setup",
			}
		):
			results = awesomebar_results("guides")

		self.assertEqual(results[0]["route"], "/app/docs/en/guides/setup")

	def test_matches_body_content(self):
		with DocsTestEnvironment(
			{
				"en/setup.md": "---\ntitle: Setup\n---\nRun bench migrate to apply patches.",
				"en/other.md": "---\ntitle: Other\n---\nNothing to see here.",
			}
		):
			results = awesomebar_results("patches")

		self.assertEqual([item["label"] for item in results], ["Setup"])
		self.assertIn("patches", results[0]["description"])

	def test_matches_word_prefix(self):
		with DocsTestEnvironment({"en/setup.md": "---\ntitle: Setup\n---\nRun bench migrate."}):
			results = awesomebar_results("migr")

		self.assertEqual([item["label"] for item in results], ["Setup"])

	def test_all_words_must_match(self):
		with DocsTestEnvironment(
			{
				"en/setup.md": "---\ntitle: Setup\n---\nRun bench migrate.",
				"en/other.md": "---\ntitle: Other\n---\nRun the tests.",
			}
		):
			results = awesomebar_results("run migrate")

		self.assertEqual([item["label"] for item in results], ["Setup"])

	def test_title_hit_ranks_above_body_hit(self):
		with DocsTestEnvironment(
			{
				"en/backup.md": "---\ntitle: Backup\n---\nHow to keep copies.",
				"en/setup.md": "---\ntitle: Setup\n---\nTake a backup first.",
			}
		):
			results = awesomebar_results("backup")

		self.assertEqual([item["label"] for item in results], ["Backup", "Setup"])

	def test_snippet_is_plain_text(self):
		with DocsTestEnvironment(
			{
				"en/setup.md": (
					"---\ntitle: Setup\n---\n## Bench\n\n"
					"*Run* <b>bench</b> [migrate](https://example.com/docs) & wait."
				),
			}
		):
			results = awesomebar_results("migrate")

		self.assertEqual(results[0]["description"], "Bench Run bench migrate &amp; wait.")

	def test_link_targets_are_not_searchable(self):
		with DocsTestEnvironment(
			{"en/setup.md": "---\ntitle: Setup\n---\nSee [the manual](https://example.com/hyperion)."}
		):
			self.assertEqual(awesomebar_results("hyperion"), [])
			self.assertEqual([item["label"] for item in awesomebar_results("manual")], ["Setup"])

	def test_index_page_route_has_no_trailing_path(self):
		with DocsTestEnvironment({"en/index.md": "---\ntitle: Home\n---\n# Home"}):
			results = awesomebar_results("home")

		self.assertEqual(results[0]["route"], "/app/docs/en")

	def test_skips_unpermitted_pages(self):
		with DocsTestEnvironment(
			{
				"en/public.md": "---\ntitle: Public Guide\nroles: Desk User\n---\n# Public",
				"en/admin.md": "---\ntitle: Admin Guide\nroles: System Manager\n---\n# Admin",
			}
		):
			frappe.set_user("test@example.com")
			with patch("compendium.docs.get_user_roles", return_value=["Desk User"]):
				results = awesomebar_results("guide")

		labels = [item["label"] for item in results]
		self.assertEqual(labels, ["Public Guide"])

	def test_index_is_reused_across_requests(self):
		with DocsTestEnvironment({"en/setup.md": "---\ntitle: Setup\n---\nRun bench migrate."}):
			index = get_index("en")
			self.next_request()
			self.assertIs(get_index("en"), index)

	def test_index_rebuilds_when_a_page_changes(self):
		with DocsTestEnvironment({"en/setup.md": "---\ntitle: Setup\n---\nRun bench migrate."}) as docs_root:
			self.assertEqual(awesomebar_results("hyphenation"), [])

			with open(os.path.join(docs_root, "en", "extra.md"), "w", encoding="utf-8") as f:
				f.write("---\ntitle: Extra\n---\nAbout hyphenation.")

			self.next_request()
			results = awesomebar_results("hyphenation")

		self.assertEqual([item["label"] for item in results], ["Extra"])
