from pathlib import Path

from pantry.db import Database

SAMPLE = Path(__file__).resolve().parent.parent / "dev" / "sample.sql"


def sample_db():
    return Database.from_sql(SAMPLE.read_text(encoding="utf-8"))
