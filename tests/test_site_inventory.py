"""Tests for the CMO site-inventory parser against the real brightpaths site."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from departments.cmo.site_inventory import inventory

SITE = Path(__file__).resolve().parent.parent / "sites" / "brightpaths"


class TestSiteInventory(unittest.TestCase):
    def test_parses_all_pages(self):
        pages = inventory(SITE)
        urls = {p["url"] for p in pages}
        self.assertIn("/", urls)
        self.assertIn("/articles/how-long-do-solar-lights-last", urls)
        self.assertEqual(len(pages), 4)

    def test_extracts_seo_fields(self):
        pages = {p["url"]: p for p in inventory(SITE)}
        home = pages["/"]
        self.assertTrue(home["title"])
        self.assertTrue(home["meta_description"])
        self.assertTrue(home["h1"])
        self.assertGreater(home["word_count"], 250)
        self.assertTrue(home["internal_links"])

    def test_missing_root_raises(self):
        with self.assertRaises(FileNotFoundError):
            inventory(SITE / "nope")


if __name__ == "__main__":
    unittest.main(verbosity=2)
