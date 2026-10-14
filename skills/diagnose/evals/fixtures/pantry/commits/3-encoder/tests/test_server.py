import json
import unittest
from urllib.parse import urlsplit

from pantry.server import handle_search, render, route
from support import sample_db


class HandleSearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = sample_db()

    def test_requires_q(self):
        status, payload = handle_search(self.db, "limit=5")
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing q")

    def test_rejects_bad_limit(self):
        status, _ = handle_search(self.db, "q=tofu&limit=ten")
        self.assertEqual(status, 400)

    def test_search(self):
        status, payload = handle_search(self.db, "q=tofu&limit=5")
        self.assertEqual(status, 200)
        self.assertEqual(payload["count"], 5)

    def test_unknown_path(self):
        status, _ = route(self.db, urlsplit("/v1/search?q=tofu"))
        self.assertEqual(status, 404)

    def test_render(self):
        body = render({"query": "tofu", "count": 0, "hits": [], "facets": []})
        self.assertIsInstance(body, bytes)
        self.assertEqual(json.loads(body)["query"], "tofu")
        self.assertTrue(body.startswith(b'{"count"'))


if __name__ == "__main__":
    unittest.main()
