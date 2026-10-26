"""Mail the kitchen the preorder sheet for tomorrow.

Runs every evening from the ops host:

    python3 -m crumb.export --for tomorrow
"""
import argparse
import sys
from datetime import datetime, timedelta

from crumb import db, mail, sheet

DATABASE = "/srv/crumb/prod/orders.db"
KITCHEN = "kitchen@crumbandco.example"


def target_date(now):
    return (now + timedelta(days=1)).date()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m crumb.export")
    parser.add_argument("--for", dest="day", required=True, choices=["tomorrow"],
                        help="which day's preorders to send")
    parser.add_argument("--db", default=DATABASE, help="orders database")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the sheet instead of mailing it")
    args = parser.parse_args(argv)
    day = target_date(datetime.now())
    orders = db.orders_for(args.db, day)
    text = sheet.render(day, orders)
    if args.dry_run:
        sys.stdout.write(text)
    else:
        mail.send(KITCHEN, sheet.subject(day, len(orders)), text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
