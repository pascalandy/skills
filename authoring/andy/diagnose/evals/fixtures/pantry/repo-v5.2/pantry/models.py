"""Recipe rows as the search API returns them."""

from dataclasses import dataclass

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

    @classmethod
    def from_row(cls, row):
        id_, slug, title, summary, tags, minutes, serves, author, updated_at = row[:9]
        tag_list = sorted(tags.split(",")) if tags else []
        return cls(id_, slug, title, summary, tag_list, minutes, serves, author, updated_at)

    @property
    def images(self):
        return {f"w{width}": f"{IMAGE_BASE}/{self.slug}/{width}.jpg" for width in IMAGE_WIDTHS}
