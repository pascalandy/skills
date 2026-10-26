import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import tally

ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args):
    proc = subprocess.run([sys.executable, "-m", "tally", *args], cwd=ROOT, capture_output=True, text=True)
    return proc.returncode, [json.loads(line) for line in proc.stdout.splitlines()]


class CliTest(unittest.TestCase):
    def test_version(self):
        self.assertEqual(run_cli("--version"), (0, [{"ok": True, "version": tally.__version__}]))

    def test_help_lists_the_commands(self):
        code, answers = run_cli("--help")
        self.assertEqual(code, 0)
        self.assertEqual(sorted(answers[0]["commands"]), ["balance", "import"])

    def test_missing_ledger_option_is_a_usage_error(self):
        code, answers = run_cli("import", "samples/birchwood-sample.csv")
        self.assertEqual(code, 2)
        self.assertFalse(answers[0]["ok"])

    def test_import_then_balance(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = str(Path(tmp) / "ledger.sqlite")
            code, answers = run_cli("import", "samples/birchwood-sample.csv", "--ledger", ledger)
            self.assertEqual((code, answers[0]["inserted"]), (0, 20))
            code, answers = run_cli("balance", "--ledger", ledger, "--account", "birchwood-chequing")
            self.assertEqual(code, 0)
            self.assertEqual(
                answers,
                [{"ok": True, "account": "birchwood-chequing", "balance": "5457.44",
                  "transactions": 20, "through": "2026-03-31"}],
            )

    def test_unrecognized_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            statement = Path(tmp) / "export.csv"
            statement.write_text("When,What,How much\n2026-03-01,Coffee,-3.00\n")
            code, answers = run_cli("import", str(statement), "--ledger", str(Path(tmp) / "ledger.sqlite"))
            self.assertEqual(code, 1)
            self.assertIn("unrecognized statement header", answers[0]["errors"][0])

    def test_balance_needs_an_existing_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "missing.sqlite")
            code, answers = run_cli("balance", "--ledger", missing, "--account", "fernhill-card")
            self.assertEqual((code, answers[0]["ok"]), (1, False))
            self.assertFalse(Path(missing).exists())
