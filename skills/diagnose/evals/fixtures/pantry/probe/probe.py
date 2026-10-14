#!/usr/bin/env python3
"""Read-only readings for the pantry-search pools.

Production readings come from .probe/data.tgz. --pool patched replays the
recorded searches against this working tree, in-process.
"""

import inspect
import json
import math
import sys
import tarfile
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / ".probe" / "data.tgz"
WINDOW = "2026-10-14 14:00-14:15 UTC"
REPLAY_NOW = "2026-10-14 14:00:00"
REPLAY_LIMIT = 24

POOLS = {
    "blue": "version=5.3.0  instances=18  threads/instance=16",
    "green": "version=5.2.0  instances=2  threads/instance=16",
}

CHECKS = {
    "latency": "request duration at the pool's load balancer (p50, p95, p99)",
    "threads": "busy worker threads per instance, and connections waiting for one",
    "cpu": "process CPU per instance",
    "gc": "garbage collector pauses per instance",
    "db-cpu": "CPU of the pool's recipe store, against Monday's same window",
    "response-size": "response body size",
    "statement-time": "time per database statement as the app measures it",
    "errors": "error responses by status",
    "cache-hit": "hit rate of the result cache in front of the pool",
    "statements": "statements per request (queries_per_request); --by-hits splits by hit count",
    "slow-requests": "five slowest traced requests, with the statements each ran",
}

PATCHED_CHECKS = {
    "statements": CHECKS["statements"],
    "response-size": "response body size, as this tree renders it",
    "latency": "time per search in-process, rendering included",
}
BUCKETS = (("0", 0, 0), ("1-5", 1, 5), ("6-12", 6, 12), ("13-24", 13, 24))

USAGE = "usage: ./probe <check> --pool blue|green|patched [--by-hits]"


def help_text():
    width = max(len(name) for name in CHECKS)
    lines = [
        USAGE,
        "",
        f"Read-only readings for pantry-search, window {WINDOW}.",
        "",
        "checks:",
    ]
    lines += [f"  {name.ljust(width)}  {text}" for name, text in CHECKS.items()]
    lines += [
        "",
        "pools (every check takes --pool):",
        "  blue     production, 5.3.0, 18 instances, 90 % of traffic",
        "  green    production, 5.2.0, 2 instances, 10 % of traffic",
        "  patched  this working tree, in-process on dev/sample.sql, replaying the 60",
        "           searches recorded on blue in the window (limit=24). It measures",
        "           statements, response-size, and latency; the other checks need a",
        "           production pool.",
        "",
        "options:",
        "  --by-hits  with statements: split by the number of hits a request returned",
    ]
    return "\n".join(lines)


def usage_error(message):
    print(f"probe: {message}", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 2


def parse(argv):
    check, pool, by_hits = None, None, False
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg in ("-h", "--help"):
            return "help", None, False
        if arg == "--by-hits":
            by_hits = True
        elif arg == "--pool":
            if not args:
                raise ValueError("--pool needs a value: blue, green, or patched")
            pool = args.pop(0)
        elif arg.startswith("--pool="):
            pool = arg.split("=", 1)[1]
        elif arg.startswith("-"):
            raise ValueError(f"unknown option: {arg}")
        elif check is None:
            check = arg
        else:
            raise ValueError(f"unexpected argument: {arg}")
    return check, pool, by_hits


def read_data():
    if not DATA.exists():
        raise FileNotFoundError(f"probe data missing: {DATA.relative_to(ROOT)}")
    files = {}
    with tarfile.open(DATA, "r:gz") as archive:
        for member in archive.getmembers():
            if member.isfile():
                name = member.name[2:] if member.name.startswith("./") else member.name
                files[name] = archive.extractfile(member).read().decode("utf-8")
    return files


def pool_reading(check, pool, by_hits):
    files = read_data()
    name = f"{check}/{pool}-by-hits.txt" if by_hits else f"{check}/{pool}.txt"
    print(f"pantry-search  pool={pool}  {POOLS[pool]}  window={WINDOW}")
    print(f"{check}: {CHECKS[check]}")
    print()
    print(files[name].rstrip("\n"))
    return 0


def percentile(values, share):
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(share * len(ordered)) - 1))
    return ordered[index]


def replay():
    """Run the recorded searches through this tree's search code."""
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT))
    import pantry
    from pantry.db import Database
    from pantry.search import search

    try:
        from pantry.server import render
    except ImportError:
        def render(payload):
            return json.dumps(payload).encode("utf-8")

    queries = [
        line.strip()
        for line in read_data()["replay/queries.txt"].splitlines()
        if line.strip() and not line.startswith("#")
    ]
    db = Database.from_sql((ROOT / "dev" / "sample.sql").read_text(encoding="utf-8"))
    kwargs = {"now": REPLAY_NOW} if "now" in inspect.signature(search).parameters else {}

    runs = []
    for q in queries:
        with db.request() as stats:
            result = search(db, q, limit=REPLAY_LIMIT, **kwargs)
            body = render(result)
        runs.append({"hits": len(result["hits"]), "statements": stats.statements, "bytes": len(body)})
    for run, q in zip(runs, queries):
        started = time.perf_counter()
        with db.request():
            render(search(db, q, limit=REPLAY_LIMIT, **kwargs))
        run["ms"] = (time.perf_counter() - started) * 1000
    return getattr(pantry, "__version__", "unknown"), runs


def patched_reading(check, by_hits):
    if check not in PATCHED_CHECKS:
        print("pantry-search  pool=patched  (this working tree)")
        print(f"{check}: not measurable for --pool patched; it needs a production pool.")
        print(f"patched measures: {', '.join(PATCHED_CHECKS)}")
        return 0
    try:
        version, runs = replay()
    except Exception as exc:
        print(f"probe: patched run failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc(limit=-3, file=sys.stderr)
        return 1

    print(f"pantry-search  pool=patched  version={version} (working tree)  "
          f"dev/sample.sql  {len(runs)} replayed searches  limit={REPLAY_LIMIT}")
    print(f"{check}: {PATCHED_CHECKS[check]}")
    print()
    if check == "statements" and by_hits:
        print("hits     searches   mean hits   mean statements")
        for label, low, high in BUCKETS + (("all", 0, 10**6),):
            group = [run for run in runs if low <= run["hits"] <= high]
            if not group:
                print(f"{label:<8} {0:>8}   {'-':>9}   {'-':>15}")
                continue
            hits = sum(run["hits"] for run in group) / len(group)
            statements = sum(run["statements"] for run in group) / len(group)
            print(f"{label:<8} {len(group):>8}   {hits:>9.1f}   {statements:>15.1f}")
    elif check == "statements":
        counts = [run["statements"] for run in runs]
        print("searches   mean   p95")
        print(f"{len(runs):>8}   {sum(counts) / len(counts):>4.1f}   {percentile(counts, 0.95):>3}")
    elif check == "response-size":
        sizes = [run["bytes"] / 1000 for run in runs]
        print("searches   mean KB   p95 KB")
        print(f"{len(runs):>8}   {sum(sizes) / len(sizes):>7.1f}   {percentile(sizes, 0.95):>6.1f}")
        print()
        print("bodies from this tree's encoder on sample data; not comparable with a pool's sizes")
    else:
        times = [run["ms"] for run in runs]
        print("searches   p50 ms   p95 ms   max ms")
        print(f"{len(runs):>8}   {percentile(times, 0.5):>6.1f}   "
              f"{percentile(times, 0.95):>6.1f}   {max(times):>6.1f}")
        print()
        print("in-process time per search on sample data, no network and no waiting for a")
        print("worker; measured on each call, so it varies a little between runs")
    return 0


def main(argv):
    if not argv:
        print(help_text())
        return 0
    try:
        check, pool, by_hits = parse(argv)
    except ValueError as exc:
        return usage_error(str(exc))
    if check == "help":
        print(help_text())
        return 0
    if check is None:
        return usage_error("missing check (see ./probe --help)")
    if check not in CHECKS:
        return usage_error(f"unknown check: {check} (see ./probe --help)")
    if pool is None:
        return usage_error("missing --pool: blue, green, or patched")
    if pool not in POOLS and pool != "patched":
        return usage_error(f"unknown pool: {pool} (blue, green, patched)")
    if by_hits and check != "statements":
        return usage_error("--by-hits applies to the statements check only")
    try:
        if pool == "patched":
            return patched_reading(check, by_hits)
        return pool_reading(check, pool, by_hits)
    except (FileNotFoundError, KeyError, tarfile.TarError) as exc:
        print(f"probe: cannot read recorded data: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
