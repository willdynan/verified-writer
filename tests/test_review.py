import json
import unittest

from verified_writer.review import build_page

CHANGES = [
    {"record_id": "r1", "payload": {"state": "closed"}, "pre": {"state": "open"}},
    {"record_id": "r2", "payload": {"owner": "cy@example.com"}, "pre": {"owner": "bo@example.com"}},
]


class ReviewPage(unittest.TestCase):
    def test_data_is_inlined(self):
        page = build_page(CHANGES, title="Batch 7")
        self.assertIn(json.dumps(CHANGES), page)
        self.assertIn("Batch 7", page)

    def test_page_is_self_contained(self):
        page = build_page(CHANGES)
        for marker in ("<script src", "<link", "fetch(", "http://", "https://"):
            self.assertNotIn(marker, page,
                             "the page must work from file:// with no network")

    def test_title_is_escaped(self):
        page = build_page(CHANGES, title="<img onerror=x>")
        self.assertNotIn("<img onerror", page)


if __name__ == "__main__":
    unittest.main()
