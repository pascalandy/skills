"""Recipe search: matching, ranking, and tag facets."""

from .models import Recipe

DEFAULT_LIMIT = 24
MAX_LIMIT = 48
MAX_TERMS = 6
FACETS = 12

COLUMNS = """r.id, r.slug, r.title, r.summary,
    (SELECT group_concat(t.tag, ',') FROM recipe_tags t WHERE t.recipe_id = r.id),
    r.total_minutes, r.serves, r.author, r.updated_at"""


def parse_terms(q):
    return q.lower().split()[:MAX_TERMS]


def match_clause(terms):
    """Every term must appear in the title or equal one of the recipe's tags."""
    clauses, params = ["r.published = 1"], []
    for term in terms:
        clauses.append(
            "(r.title LIKE ? OR EXISTS (SELECT 1 FROM recipe_tags t"
            " WHERE t.recipe_id = r.id AND t.tag = ?))"
        )
        params += [f"%{term}%", term]
    return " AND ".join(clauses), params


def search(db, q, limit=DEFAULT_LIMIT):
    terms = parse_terms(q)
    limit = max(1, min(limit, MAX_LIMIT))
    where, params = match_clause(terms)
    score = " + ".join(["(r.title LIKE ?) * 2"] * len(terms)) or "0"
    score_params = [f"%{term}%" for term in terms]
    rows = db.query(
        f"SELECT {COLUMNS}, {score} AS score FROM recipes r WHERE {where}"
        " ORDER BY score DESC, r.saves DESC, r.id LIMIT ?",
        score_params + params + [limit],
    )
    recipes = [Recipe.from_row(row, db) for row in rows]
    facets = db.query(
        "SELECT t.tag, count(*) AS n FROM recipe_tags t"
        f" WHERE t.recipe_id IN (SELECT r.id FROM recipes r WHERE {where})"
        " GROUP BY t.tag ORDER BY n DESC, t.tag LIMIT ?",
        params + [FACETS],
    )
    return {
        "query": q,
        "count": len(recipes),
        "hits": [hit_json(recipe) for recipe in recipes],
        "facets": [{"tag": tag, "count": n} for tag, n in facets],
    }


def hit_json(recipe):
    return {
        "id": recipe.id,
        "slug": recipe.slug,
        "title": recipe.title,
        "summary": recipe.summary,
        "tags": recipe.tags,
        "minutes": recipe.total_minutes,
        "serves": recipe.serves,
        "author": recipe.author,
        "url": f"/recipes/{recipe.slug}",
        "images": recipe.images,
        "rating": recipe.rating,
    }
