#!/usr/bin/env python3
"""Import each sample statement into a fresh ledger and compare the readings with the last good run.

Usage: python3 skills/verify-tally/scripts/smoke.py [--record]
"""

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ROOT = SKILL.parent.parent
LAST_GOOD = SKILL / "runs" / "last-good.json"
READINGS = ("inserted",)


def import_sample(path, ledger):
    proc = subprocess.run(
        [sys.executable, "-m", "tally", "import", str(path), "--ledger", str(ledger)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if not proc.stdout.strip():
        raise SystemExit("%s: tally printed nothing (exit %d)\n%s" % (path.name, proc.returncode, proc.stderr))
    answer = json.loads(proc.stdout)
    if not answer.get("ok"):
        raise SystemExit("%s: %s" % (path.name, "; ".join(answer.get("errors", []))))
    return {name: answer[name] for name in READINGS}


def main():
    parser = argparse.ArgumentParser(description="Smoke import of samples/, compared with runs/last-good.json.")
    parser.add_argument("--record", action="store_true", help="write this run's readings to runs/last-good.json")
    args = parser.parse_args()

    last_good = json.loads(LAST_GOOD.read_text())["samples"] if LAST_GOOD.exists() else {}
    current = {}
    all_match = True
    with tempfile.TemporaryDirectory() as tmp:
        for path in sorted((ROOT / "samples").glob("*.csv")):
            readings = import_sample(path, Path(tmp) / (path.stem + ".sqlite"))
            expected = last_good.get(path.stem)
            match = readings == expected
            all_match = all_match and match
            current[path.stem] = readings
            line = {"sample": path.stem, "readings": readings, "last_good": expected, "match": match}
            print(json.dumps(line, separators=(",", ":")))

    if args.record:
        record = {"recorded": date.today().isoformat(), "samples": current}
        LAST_GOOD.write_text(json.dumps(record, indent=2) + "\n")
        return 0
    return 0 if all_match else 1


if __name__ == "__main__":
    sys.exit(main())
