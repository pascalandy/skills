import unittest

from pantry.search import MAX_LIMIT, search
from support import sample_db


class SearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = sample_db()

    def find(self, q, **kwargs):
        return search(self.db, q, **kwargs)

    def test_single_term_fills_the_page(self):
        result = self.find("chicken")
        self.assertEqual(result["count"], 24)
        for hit in result["hits"]:
            self.assertTrue("chicken" in hit["title"].lower() or "chicken" in hit["tags"])

    def test_every_term_must_match(self):
        result = self.find("salmon curry")
        self.assertGreater(result["count"], 0)
        for hit in result["hits"]:
            self.assertIn("salmon", hit["title"].lower())
            self.assertIn("curry", hit["title"].lower())

    def test_tags_match_exactly(self):
        result = self.find("vegetarian")
        self.assertEqual(result["count"], 24)
        for hit in result["hits"]:
            self.assertIn("vegetarian", hit["tags"])

    def test_no_match(self):
        result = self.find("durian")
        self.assertEqual(result["hits"], [])
        self.assertEqual(result["facets"], [])

    def test_limit_is_capped(self):
        self.assertEqual(self.find("vegetarian", limit=500)["count"], MAX_LIMIT)
        self.assertEqual(self.find("vegetarian", limit=0)["count"], 1)

    def test_unpublished_recipes_are_hidden(self):
        hidden = self.db.query("SELECT id, title FROM recipes WHERE published = 0")
        self.assertTrue(hidden)
        for recipe_id, title in hidden:
            ids = {hit["id"] for hit in self.find(title, limit=MAX_LIMIT)["hits"]}
            self.assertNotIn(recipe_id, ids)

    def test_facets_count_matching_recipes(self):
        facets = {f["tag"]: f["count"] for f in self.find("tofu")["facets"]}
        (published,) = self.db.query(
            "SELECT count(*) FROM recipes r JOIN recipe_tags t ON t.recipe_id = r.id"
            " WHERE t.tag = 'tofu' AND r.published = 1"
        )[0]
        self.assertEqual(facets["tofu"], published)
        self.assertEqual(facets["vegetarian"], published)

    def test_hits_link_to_recipe_pages(self):
        hit = self.find("miso")["hits"][0]
        self.assertEqual(hit["url"], f"/recipes/{hit['slug']}")
        self.assertEqual(sorted(hit["images"]), ["w1280", "w320", "w640"])


if __name__ == "__main__":
    unittest.main()
