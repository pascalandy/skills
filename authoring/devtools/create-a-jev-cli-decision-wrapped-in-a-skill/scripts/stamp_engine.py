#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Rewrite the source-hash stamp in the canonical jevgate.py after an edit."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().with_name("jevgate.py")
STAMPS = (b"# jevgate-version:", b"# jevgate-hash:")

EPILOG = """\
examples:
  just stamp-jevgate
  just stamp-jevgate --dry-run

exit codes: 0 ok, 1 failure, 2 bad usage, 130 interrupted"""


def stamp(dry_run: bool) -> str:
    source = ENGINE.read_bytes()
    lines = source.splitlines(keepends=True)
    kept = b"".join(line for line in lines if not line.startswith(STAMPS))
    actual = "sha256:" + hashlib.sha256(kept).hexdigest()
    hash_lines = [
        index for index, line in enumerate(lines) if line.startswith(STAMPS[1])
    ]
    if len(hash_lines) != 1:
        raise ValueError(f"{ENGINE.name} needs exactly one '# jevgate-hash:' line")
    current = lines[hash_lines[0]].split(b":", 1)[1].strip().decode()
    if current == actual:
        return f"ok: {ENGINE.name} already stamped {actual}"
    if dry_run:
        return f"dry run: would stamp {ENGINE.name} {actual} (was {current})"
    lines[hash_lines[0]] = f"# jevgate-hash: {actual}\n".encode()
    ENGINE.write_bytes(b"".join(lines))
    return f"ok: stamped {ENGINE.name} {actual}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="just stamp-jevgate",
        description="Stamp the canonical jevgate.py with the hash of its source",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="report the new stamp without writing"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="print tracebacks on stderr"
    )
    args = parser.parse_args(argv)
    try:
        print(stamp(args.dry_run))
        return 0
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except (OSError, ValueError) as error:
        if args.verbose:
            raise
        print(f"error: {error}; check the engine file and rerun", file=sys.stderr)
        print("rerun with --verbose for details", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
