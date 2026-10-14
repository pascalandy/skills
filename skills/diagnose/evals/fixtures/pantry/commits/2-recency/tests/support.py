from pathlib import Path

from pantry.db import Database

SAMPLE = Path(__file__).resolve().parent.parent / "dev" / "sample.sql"
NOW = "2026-10-01 12:00:00"


def sample_db():
    return Database.from_sql(SAMPLE.read_text(encoding="utf-8"))
