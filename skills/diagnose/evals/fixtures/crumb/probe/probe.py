#!/usr/bin/env python3
"""Read-only checks on the Crumb & Co. ops hosts and order databases."""
import re
import sys
import tarfile
from pathlib import Path

DATA = Path(__file__).resolve().parent / ".probe" / "data.tgz"
HOSTS = ("ops-1", "ops-2")
ENVS = ("prod", "staging")
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")

HELP = """\
usage: ./probe <check> [options]

Read-only checks on the Crumb & Co. ops hosts and order databases.
ops-1 is powered off: its answers come from the backup of its config
and logs taken at shutdown, 2026-10-09 10:00 EDT.

checks:
  unit      --host ops-1|ops-2                   how the preorder export is scheduled (crontab, or timer and service)
  env       --host ops-1|ops-2                   environment the preorder export process gets
  timezone  --host ops-1|ops-2                   system time zone and clock, as timedatectl prints them
  python    --host ops-1|ops-2                   interpreter path and version
  journal   --host ops-1|ops-2 [--since DATE]    preorder export runs and their log lines
  orders    --env prod|staging [--date DATE]     orders per pickup date (cancelled left out)
  sync-log  --env prod|staging                   orders sync runs per day: status and rows
  mail-log                                       sheets the mail relay delivered to the kitchen

DATE is YYYY-MM-DD.
"""

CHECKS = {
    "unit": ({"--host"}, {"--host"}),
    "env": ({"--host"}, {"--host"}),
    "timezone": ({"--host"}, {"--host"}),
    "python": ({"--host"}, {"--host"}),
    "journal": ({"--host", "--since"}, {"--host"}),
    "orders": ({"--env", "--date"}, {"--env"}),
    "sync-log": ({"--env"}, {"--env"}),
    "mail-log": (set(), set()),
}


def fail(message):
    print(f"probe: {message}", file=sys.stderr)
    sys.exit(2)


def read(name):
    try:
        with tarfile.open(DATA) as tar:
            for member in tar.getmembers():
                if member.name.lstrip("./") == name:
                    return tar.extractfile(member).read().decode()
    except (OSError, tarfile.TarError) as exc:
        fail(f"cannot read {DATA}: {exc}")
    fail(f"no data for {name}")


def parse(check, args):
    allowed, required = CHECKS[check]
    opts = {}
    while args:
        key = args.pop(0)
        if "=" in key:
            key, value = key.split("=", 1)
        elif args:
            value = args.pop(0)
        else:
            fail(f"{check}: {key} needs a value")
        if key not in allowed:
            fail(f"{check}: unknown option {key}")
        opts[key] = value
    for key in sorted(required - opts.keys()):
        fail(f"{check}: {key} is required")
    if "--host" in opts and opts["--host"] not in HOSTS:
        fail(f"unknown host {opts['--host']!r} (hosts: {', '.join(HOSTS)})")
    if "--env" in opts and opts["--env"] not in ENVS:
        fail(f"unknown env {opts['--env']!r} (envs: {', '.join(ENVS)})")
    for key in ("--since", "--date"):
        if key in opts and not DAY.match(opts[key]):
            fail(f"{check}: {key} wants YYYY-MM-DD, got {opts[key]!r}")
    return opts


def journal(host, since):
    shown = []
    for row in read(f"journal-{host}.txt").splitlines():
        key, _, text = row.partition("\t")
        if key == "-" or since is None or key >= since:
            shown.append(text)
    while shown and not shown[-1].strip():
        shown.pop()
    if not any(line.strip() and not line.startswith(("syslog", "/var/mail")) for line in shown):
        shown.append("-- No entries --")
    return "\n".join(shown) + "\n"


def orders(env, day):
    rows = [line.split("\t") for line in read("orders.tsv").splitlines() if line]
    column = 1 if env == "prod" else 2
    if day:
        for row in rows:
            if row[0] == day:
                return f"env {env}, pickup date {day}: {row[column]} orders\n"
        fail(f"orders: --date must be between {rows[0][0]} and {rows[-1][0]}")
    out = [f"env {env}, orders per pickup date", "pickup date   orders"]
    out += [f"{row[0]}  {int(row[column]):6d}" for row in rows]
    return "\n".join(out) + "\n"


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        sys.stdout.write(HELP)
        return 0
    check, args = argv[0], list(argv[1:])
    if check not in CHECKS:
        fail(f"unknown check {check!r}; ./probe --help lists them")
    opts = parse(check, args)
    host, env = opts.get("--host"), opts.get("--env")
    if check in ("unit", "env", "timezone", "python"):
        out = read(f"{check}-{host}.txt")
    elif check == "journal":
        out = journal(host, opts.get("--since"))
    elif check == "orders":
        out = orders(env, opts.get("--date"))
    elif check == "sync-log":
        out = read(f"sync-{env}.txt")
    else:
        out = read("mail-log.txt")
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
