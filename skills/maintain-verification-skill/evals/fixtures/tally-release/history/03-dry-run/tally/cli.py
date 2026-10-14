"""Command line: python3 -m tally <command>. Every command answers with one JSON line."""

import argparse
import json
import os
import sqlite3
import sys

from tally import __version__
from tally.importer import import_statement
from tally.ledger import Ledger, LedgerError, money

HELP = {
    "usage": "python3 -m tally <command> [options]",
    "commands": {
        "import": "import <statement.csv> --ledger <ledger.sqlite> [--dry-run]",
        "balance": "balance --ledger <ledger.sqlite> --account <name>",
    },
    "options": {"--version": "print the version", "--help": "print this help"},
}


class UsageError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def build_parser():
    parser = Parser(prog="tally", add_help=False)
    parser.add_argument("--version", action="store_true")
    commands = parser.add_subparsers(dest="command")
    imp = commands.add_parser("import", add_help=False)
    imp.add_argument("statement")
    imp.add_argument("--ledger", required=True)
    imp.add_argument("--dry-run", action="store_true")
    bal = commands.add_parser("balance", add_help=False)
    bal.add_argument("--ledger", required=True)
    bal.add_argument("--account", required=True)
    return parser


def emit(answer):
    print(json.dumps(answer, separators=(",", ":")))


def run(args):
    if args.command == "import":
        answer = import_statement(args.statement, args.ledger, dry_run=args.dry_run)
        if args.dry_run:
            answer["dry_run"] = True
        return answer
    if not os.path.exists(args.ledger):
        raise LedgerError("no ledger at %s" % args.ledger)
    with Ledger(args.ledger) as ledger:
        balance, count, through = ledger.balance(args.account)
    return {"account": args.account, "balance": money(balance), "transactions": count, "through": through}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--help" in argv or "-h" in argv:
        emit(dict(ok=True, **HELP))
        return 0
    try:
        args = build_parser().parse_args(argv)
        if not args.version and args.command is None:
            raise UsageError("a command is required: import or balance")
    except UsageError as exc:
        emit({"ok": False, "errors": [str(exc)]})
        return 2
    if args.version:
        emit({"ok": True, "version": __version__})
        return 0
    try:
        answer = run(args)
    except (OSError, ValueError, LedgerError, sqlite3.Error) as exc:
        emit({"ok": False, "errors": [str(exc)]})
        return 1
    emit(dict(ok=True, **answer))
    return 0
