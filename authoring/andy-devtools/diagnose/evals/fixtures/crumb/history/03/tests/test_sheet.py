import unittest
from datetime import date

from crumb import sheet
from crumb.db import Order


def order(id, pickup="08:00", customer="Ines Halloran", items="1 country loaf", note=""):
    return Order(id, pickup, customer, items, note)


class SheetTest(unittest.TestCase):
    def test_title_names_the_day(self):
        self.assertEqual(sheet.title(date(2026, 3, 14)), "Orders for Sat 2026-03-14")

    def test_subject_has_count(self):
        self.assertEqual(sheet.subject(date(2026, 3, 16), 7), "Preorders for Mon 2026-03-16 (7)")

    def test_line(self):
        self.assertEqual(
            sheet.line(order(1001)),
            "08:00  #1001  Ines Halloran         1 country loaf",
        )

    def test_render(self):
        text = sheet.render(date(2026, 3, 14), [order(1001), order(1002, pickup="09:30")])
        self.assertEqual(text.splitlines()[0], "Orders for Sat 2026-03-14")
        self.assertEqual(len(text.splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
