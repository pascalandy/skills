"""Mail the kitchen the preorder sheet for tomorrow.

Runs every evening from the ops host:

    python3 -m crumb.export --for tomorrow
"""
import argparse
import sqlite3
import sys
from datetime import datetime, timedelta

from crumb import db, mail, sheet

KITCHEN = "kitchen@crumbandco.example"


def target_date(now):
    return (now + timedelta(days=1)).date()


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="python3 -m crumb.export",
        description="Send the kitchen the preorder sheet.",
    )
    parser.add_argument("--for", dest="day", required=True, choices=["tomorrow"],
                        help="which day's preorders to send")
    parser.add_argument("--db", default="prod",
                        help="database path, or prod or staging (default: prod)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the sheet instead of mailing it")
    parser.add_argument("--now", metavar="ISO_TIME",
                        help="use this time as the current time (for tests)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.now:
        try:
            now = datetime.fromisoformat(args.now).astimezone()
        except ValueError:
            print(f"crumb.export: --now: not an ISO time: {args.now}", file=sys.stderr)
            return 2
    else:
        now = datetime.now()
    day = target_date(now)
    try:
        orders = db.orders_for(args.db, day)
    except sqlite3.Error as exc:
        print(f"crumb.export: {db.resolve(args.db)}: {exc}", file=sys.stderr)
        return 1
    print(f"target date {day.isoformat()}, {len(orders)} orders", file=sys.stderr)
    text = sheet.render(day, orders)
    if args.dry_run:
        sys.stdout.write(text)
    else:
        mail.send(KITCHEN, sheet.subject(day, len(orders)), text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
