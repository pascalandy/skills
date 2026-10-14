import unittest
from pathlib import Path

from tally import formats
from tally.formats import birchwood, fernhill
from tally.importer import read_statement
from tally.ledger import Entry, cents, money

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


class DetectTest(unittest.TestCase):
    def test_birchwood_header(self):
        self.assertIs(formats.detect(["Date", "Description", "Amount", "Balance", "Page"]), birchwood)

    def test_fernhill_header(self):
        self.assertIs(formats.detect(["Posted", "Payee", "Amount"]), fernhill)

    def test_unknown_header(self):
        with self.assertRaises(formats.UnknownFormat):
            formats.detect(["Date", "Memo", "Debit", "Credit"])


class AmountTest(unittest.TestCase):
    def test_cents(self):
        self.assertEqual(cents("-431.18"), -43118)
        self.assertEqual(cents(" 2486.30 "), 248630)
        self.assertEqual(cents("0.05"), 5)

    def test_not_an_amount(self):
        with self.assertRaises(ValueError):
            cents("12,50")

    def test_money(self):
        self.assertEqual(money(-43118), "-431.18")
        self.assertEqual(money(-5), "-0.05")
        self.assertEqual(money(248630), "2486.30")


class BirchwoodTest(unittest.TestCase):
    def setUp(self):
        self.fmt, self.rows = read_statement(SAMPLES / "birchwood-sample.csv")

    def test_detected(self):
        self.assertIs(self.fmt, birchwood)

    def test_entries(self):
        entries = birchwood.entries(self.rows)
        self.assertEqual(len(entries), 20)
        self.assertEqual(entries[0], Entry("2026-03-02", "POS GROCERS ROW #112", -6341))

    def test_opening_balance(self):
        self.assertEqual(birchwood.opening_balance(self.rows), 214062)

    def test_statement_total_is_closing_minus_opening(self):
        self.assertEqual(birchwood.statement_total(self.rows), 545744 - 214062)

    def test_statement_total_of_an_empty_export(self):
        self.assertIsNone(birchwood.statement_total([]))


class FernhillTest(unittest.TestCase):
    def setUp(self):
        self.fmt, self.rows = read_statement(SAMPLES / "fernhill-sample.csv")

    def test_detected(self):
        self.assertIs(self.fmt, fernhill)

    def test_total_line_is_not_an_entry(self):
        entries = fernhill.entries(self.rows)
        self.assertEqual(len(entries), 14)
        self.assertEqual(entries[-1], Entry("2026-03-30", "Metro Fare", -325))

    def test_posted_dates_become_iso(self):
        self.assertEqual(fernhill.entries(self.rows)[0].date, "2026-03-02")

    def test_opening_balance_is_zero(self):
        self.assertEqual(fernhill.opening_balance(self.rows), 0)

    def test_statement_total_is_the_total_line(self):
        self.assertEqual(fernhill.statement_total(self.rows), 39022)

    def test_no_total_line(self):
        self.assertIsNone(fernhill.statement_total(self.rows[:-1]))
