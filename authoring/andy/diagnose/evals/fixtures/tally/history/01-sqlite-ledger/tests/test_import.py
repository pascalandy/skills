import shutil
import tempfile
import unittest
from pathlib import Path

from tally.importer import import_statement
from tally.ledger import Ledger

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


class ImportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ledger = str(Path(self.tmp) / "ledger.sqlite")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_import(self, name, **options):
        return import_statement(str(SAMPLES / name), self.ledger, **options)

    def test_birchwood_sample(self):
        result = self.run_import("birchwood-sample.csv")
        self.assertEqual(result["file"], "birchwood-sample.csv")
        self.assertEqual(result["account"], "birchwood-chequing")
        self.assertEqual((result["rows_read"], result["inserted"], result["deduped"]), (20, 20, 0))

    def test_reimport_adds_nothing(self):
        self.run_import("birchwood-sample.csv")
        result = self.run_import("birchwood-sample.csv")
        self.assertEqual((result["inserted"], result["deduped"]), (0, 20))

    def test_fernhill_reimport_adds_nothing(self):
        first = self.run_import("fernhill-sample.csv")
        second = self.run_import("fernhill-sample.csv")
        self.assertEqual((first["account"], first["rows_read"]), ("fernhill-card", 14))
        self.assertEqual(second["inserted"], 0)

    def test_balance_is_the_closing_balance(self):
        self.run_import("birchwood-sample.csv")
        with Ledger(self.ledger) as ledger:
            self.assertEqual(ledger.balance("birchwood-chequing"), (545744, 20, "2026-03-31"))
