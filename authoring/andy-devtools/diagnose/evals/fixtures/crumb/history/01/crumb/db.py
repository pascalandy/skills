"""Preorders from the orders database (SQLite, kept current by crumb-sync)."""
import sqlite3
from dataclasses import dataclass


@dataclass
class Order:
    id: int
    pickup: str
    customer: str
    items: str
    note: str


def orders_for(path, day):
    con = sqlite3.connect(path)
    try:
        rows = con.execute(
            "SELECT id, pickup_time, customer, items, note FROM orders"
            " WHERE pickup_date = ? AND status != 'cancelled' ORDER BY id",
            (day.isoformat(),),
        ).fetchall()
    finally:
        con.close()
    return [Order(*row) for row in rows]
