import json
import unittest

from pantry.encode import dumps


class EncodeTest(unittest.TestCase):
    def test_keys_are_sorted(self):
        self.assertTrue(dumps({"b": 1, "a": 2}).startswith('{"a"'))
        self.assertEqual(dumps({"b": {"y": 1, "x": 2}}), dumps({"b": {"x": 2, "y": 1}}))

    def test_floats_are_rounded(self):
        self.assertEqual(json.loads(dumps({"stars": 4.285714})), {"stars": 4.29})

    def test_nested_values(self):
        payload = {"hits": [{"rating": {"stars": 3.14159, "count": 7}}], "pair": (2.71828, None)}
        self.assertEqual(
            json.loads(dumps(payload)),
            {"hits": [{"rating": {"stars": 3.14, "count": 7}}], "pair": [2.72, None]},
        )

    def test_text_stays_readable(self):
        self.assertIn("crème fraîche", dumps({"title": "Leeks with crème fraîche"}))


if __name__ == "__main__":
    unittest.main()
