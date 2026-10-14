"""Preorders from the orders database (SQLite, kept current by crumb-sync)."""
import os
import sqlite3
from dataclasses import dataclass

NAMED = ("prod", "staging")


@dataclass
class Order:
    id: int
    pickup: str
    customer: str
    items: str
    note: str


def resolve(db):
    """Turn `prod` or `staging` into the shared database path; leave paths alone."""
    if db in NAMED:
        base = os.environ.get("CRUMB_DATA", "/srv/crumb")
        return os.path.join(base, db, "orders.db")
    return db


def orders_for(db, day):
    """Orders to pick up on `day`, by pickup time. Cancelled orders are left out."""
    con = sqlite3.connect(f"file:{resolve(db)}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT id, pickup_time, customer, items, note FROM orders"
            " WHERE pickup_date = ? AND status != 'cancelled'"
            " ORDER BY pickup_time, id",
            (day.isoformat(),),
        ).fetchall()
    finally:
        con.close()
    return [Order(*row) for row in rows]
