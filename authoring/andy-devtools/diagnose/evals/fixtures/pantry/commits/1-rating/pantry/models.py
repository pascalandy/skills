"""Recipe rows as the search API returns them."""

from dataclasses import dataclass, field

IMAGE_BASE = "https://img.pantry.example/recipes"
IMAGE_WIDTHS = (320, 640, 1280)


@dataclass
class Recipe:
    id: int
    slug: str
    title: str
    summary: str
    tags: list
    total_minutes: int
    serves: int
    author: str
    updated_at: str
    db: object = field(default=None, repr=False, compare=False)

    @classmethod
    def from_row(cls, row, db=None):
        id_, slug, title, summary, tags, minutes, serves, author, updated_at = row[:9]
        tag_list = sorted(tags.split(",")) if tags else []
        return cls(id_, slug, title, summary, tag_list, minutes, serves, author, updated_at, db)

    @property
    def images(self):
        return {f"w{width}": f"{IMAGE_BASE}/{self.slug}/{width}.jpg" for width in IMAGE_WIDTHS}

    @property
    def rating(self):
        stars, count = self.db.query(
            "SELECT avg(stars), count(*) FROM reviews WHERE recipe_id = ?", (self.id,)
        )[0]
        return {"stars": stars, "count": count}
