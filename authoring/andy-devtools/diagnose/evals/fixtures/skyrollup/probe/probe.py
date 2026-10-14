#!/usr/bin/env python3
"""Read-only reads on wx-1 and the site CDN."""
import datetime as dt
import hashlib
import os
import re
import sys
import tarfile
from pathlib import Path

DATA = Path(__file__).resolve().parent / ".probe" / "data.tgz"
YEAR = 2026
UTC = dt.timezone.utc
HOSTS = ("wx-1", "cdn")
ROOTS = ("/srv/www", "/var/lib/skyrollup", "/var/log/skyrollup")
UNITS = {"skyrollup": "skyrollup", "radar-tiles": "radar-tiles", "www-deploy": "www-deploy"}
LEVELS = {"debug": 10, "info": 20, "warning": 30, "error": 40}
LINE_LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40, "CRITICAL": 50}
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}
SITE = "https://www.fernlowwx.example"

HELP = """\
usage: ./probe [--host HOST] CHECK [ARGS]

Read-only reads on wx-1 (the skyrollup host) and the site CDN.

checks:
  status                                        skyrollup status, on wx-1
  logs [--level L] [--since YYYY-MM-DD]         skyrollup logs, on wx-1 (L: debug, info, warning, error; default warning)
  journal --unit U [--since YYYY-MM-DD] [-n N]  journalctl -u U, on wx-1 (U: skyrollup, radar-tiles, www-deploy)
  timers                                        systemctl list-timers, on wx-1
  stat PATH                                     stat PATH, on wx-1 (under /srv/www, /var/lib/skyrollup, /var/log/skyrollup)
  ls PATH                                       ls -la --time-style=full-iso PATH, on wx-1 (same folders as stat)
  id USER                                       id USER, on wx-1 (USER: skyrollup, radar, deploy)
  cdn-headers PATH                              response headers for a site path, through the CDN (host cdn)
  origin-headers PATH                           response headers for a site path, from wx-1 directly
  deploy-log                                    www-deploy releases on wx-1 and their steps, last four weeks

hosts: wx-1 (every check but cdn-headers), cdn (cdn-headers)
"""


class Usage(Exception):
    pass


def load():
    with tarfile.open(DATA) as tar:
        return {
            m.name.removeprefix("./"): tar.extractfile(m).read().decode("utf-8")
            for m in tar.getmembers()
            if m.isfile()
        }


def h(*parts):
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return int(digest[:12], 16) / float(1 << 48)


def parse_since(value):
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(value, fmt).replace(tzinfo=UTC)
        except ValueError:
            pass
    raise Usage(f"--since takes YYYY-MM-DD, not {value!r}")


def options(args, spec):
    """Parse --name VALUE pairs; spec maps each accepted flag to its key."""
    out = {}
    rest = list(args)
    while rest:
        flag = rest.pop(0)
        if "=" in flag and flag.startswith("--"):
            flag, value = flag.split("=", 1)
            rest.insert(0, value)
        if flag not in spec or not rest:
            raise Usage(f"unexpected argument {flag!r}")
        out[spec[flag]] = rest.pop(0)
    return out


# ------------------------------------------------------------------ checks


def check_status(data, args):
    if args:
        raise Usage("status takes no arguments")
    sys.stdout.write(data["status.txt"])
    return 0


def check_logs(data, args):
    opts = options(args, {"--level": "level", "--since": "since"})
    level = opts.get("level", "warning")
    if level not in LEVELS:
        raise Usage(f"--level takes one of {', '.join(LEVELS)}")
    since = opts.get("since")
    if since:
        parse_since(since)
    for line in data["skyrollup.log"].splitlines():
        fields = line.split(" ", 3)
        if len(fields) < 4 or fields[2] not in LINE_LEVELS:
            continue
        if since and fields[0] < since[:10]:
            continue
        if LINE_LEVELS[fields[2]] >= LEVELS[level]:
            print(line)
    return 0


def journal_time(line):
    month, day, clock = line.split(" ", 3)[:3]
    hh, mm, ss = map(int, clock.split(":"))
    return dt.datetime(YEAR, MONTHS[month], int(day), hh, mm, ss, tzinfo=UTC)


def radar_lines(text):
    desc = "Radar tile refresh"
    lines = []
    for row in text.split("\n"):
        if not row.strip():
            continue
        start, pid, seconds, tiles = row.split()
        begin = dt.datetime.fromisoformat(start).replace(tzinfo=UTC)
        end = begin + dt.timedelta(seconds=float(seconds))
        b, e = begin.strftime("%b %d %H:%M:%S"), end.strftime("%b %d %H:%M:%S")
        cpu = float(seconds) * 0.31
        lines += [
            f"{b} wx-1 systemd[1]: Starting radar-tiles.service - {desc}...",
            f"{e} wx-1 radar-tiles[{pid}]: frame {begin:%Y-%m-%dT%H:%MZ}: {tiles} tiles written to /srv/www/radar/tiles",
            f"{e} wx-1 systemd[1]: radar-tiles.service: Deactivated successfully.",
            f"{e} wx-1 systemd[1]: Finished radar-tiles.service - {desc}.",
            f"{e} wx-1 systemd[1]: radar-tiles.service: Consumed {cpu:.3f}s CPU time, {18 + h(start) * 3:.1f}M memory peak.",
        ]
    return lines


def check_journal(data, args):
    args = ["--unit" if a == "-u" else a for a in args]
    opts = options(args, {"--unit": "unit", "--since": "since", "-n": "lines", "--lines": "lines"})
    unit = opts.get("unit", "").removesuffix(".service")
    if not unit:
        raise Usage("journal needs --unit (skyrollup, radar-tiles, www-deploy)")
    if unit not in UNITS:
        raise Usage(f"unknown unit {unit!r}; journal reads skyrollup, radar-tiles, www-deploy")
    if unit == "radar-tiles":
        lines = radar_lines(data["journal/radar-tiles.runs"])
    else:
        lines = data[f"journal/{unit}.txt"].splitlines()
    if "since" in opts:
        since = parse_since(opts["since"])
        lines = [line for line in lines if journal_time(line) >= since]
    if "lines" in opts:
        if opts["lines"] != "all":
            try:
                count = int(opts["lines"])
            except ValueError:
                raise Usage("-n takes a number or all")
            lines = lines[-count:] if count > 0 else []
    if not lines:
        print("-- No entries --")
    for line in lines:
        print(line)
    return 0


def check_timers(data, args):
    if args:
        raise Usage("timers takes no arguments")
    sys.stdout.write(data["timers.txt"])
    return 0


def check_id(data, args):
    if len(args) != 1:
        raise Usage("id takes one user")
    for line in data["id.txt"].splitlines():
        name, rest = line.split(" ", 1)
        if name == args[0]:
            print(rest)
            return 0
    print(f"id: '{args[0]}': no such user", file=sys.stderr)
    return 1


def check_deploy_log(data, args):
    if args:
        raise Usage("deploy-log takes no arguments")
    sys.stdout.write(data["deploy-log.txt"])
    return 0


# ------------------------------------------------------------------ files


def blocks(text):
    out = {}
    key = None
    for line in text.splitlines():
        if line.startswith("== "):
            key = line[3:]
            out[key] = []
        elif key is not None:
            out[key].append(line)
    return out


def norm_path(path):
    if not path.startswith("/"):
        raise Usage(f"{path!r}: give an absolute path")
    path = re.sub(r"/+", "/", path)
    if len(path) > 1:
        path = path.rstrip("/")
    if not any(path == root or path.startswith(root + "/") for root in ROOTS):
        raise Usage(f"{path}: this probe reads only under {', '.join(ROOTS)}")
    return path


LS_LINE = re.compile(
    r"^(?P<mode>\S{10}) +(?P<links>\d+) (?P<user>\S+) +(?P<group>\S+) +(?P<size>\d+) "
    r"(?P<when>\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{9} \+0000) (?P<name>.+)$")


def ls_entry(listings, path):
    parent, name = path.rsplit("/", 1)
    for line in listings.get(parent or "/", []):
        m = LS_LINE.match(line)
        if m and m["name"].split(" -> ")[0] == name:
            return m
    return None


def check_ls(data, args):
    if len(args) != 1:
        raise Usage("ls takes one path")
    path = norm_path(args[0])
    listings = blocks(data["ls.txt"])
    if path in listings:
        print("\n".join(listings[path]))
        return 0
    m = ls_entry(listings, path)
    if m:
        print(re.sub(r" \S+( -> \S+)?$", lambda x: " " + path + (x.group(1) or ""), m.string))
        return 0
    print(f"ls: cannot access '{path}': No such file or directory", file=sys.stderr)
    return 2


USERS = {"skyrollup": 987, "radar": 986, "deploy": 1001, "root": 0}
GROUPS = {"skyrollup": 985, "radar": 984, "deploy": 1001, "www": 1050, "root": 0, "syslog": 107}


def octal(mode):
    bits = 0
    for i, ch in enumerate(mode[1:]):
        if ch != "-":
            bits |= 1 << (8 - i)
    return f"{bits:04o}"


def check_stat(data, args):
    if len(args) != 1:
        raise Usage("stat takes one path")
    path = norm_path(args[0])
    text = data["stat.txt"].splitlines()
    for i, line in enumerate(text):
        if line == f"  File: {path}" or line.startswith(f"  File: {path} -> "):
            print("\n".join(text[i:i + 8]))
            return 0
    m = ls_entry(blocks(data["ls.txt"]), path)
    if not m:
        print(f"stat: cannot statx '{path}': No such file or directory", file=sys.stderr)
        return 1
    mode, size = m["mode"], int(m["size"])
    kind = {"d": "directory", "-": "regular file", "l": "symbolic link"}[mode[0]]
    used = 0 if mode[0] == "l" else ((size + 4095) // 4096) * 8
    target = m["name"].split(" -> ", 1)[1] if " -> " in m["name"] else None
    when = m["when"]
    print("\n".join([
        f"  File: {path}" + (f" -> {target}" if target else ""),
        f"  Size: {size:<10}\tBlocks: {used:<10} IO Block: 4096   {kind}",
        f"Device: 259,2\tInode: {1300000 + int(h('ino', path) * 90000):<11} Links: {m['links']}",
        f"Access: ({octal(mode)}/{mode})  Uid: ({USERS[m['user']]:>5}/{m['user']:>8})   "
        f"Gid: ({GROUPS[m['group']]:>5}/{m['group']:>8})",
        f"Access: {when}",
        f"Modify: {when}",
        f"Change: {when}",
        f" Birth: {when}",
    ]))
    return 0


# ------------------------------------------------------------------ http


def site_path(value):
    if value.startswith(SITE):
        value = value[len(SITE):] or "/"
    if not value.startswith("/"):
        raise Usage(f"{value!r}: give a site path such as /summaries/summary-latest.json")
    return value


def http_date(moment):
    return moment.strftime("%a, %d %b %Y %H:%M:%S GMT")


def headers(data, where, args):
    if len(args) != 1:
        raise Usage(f"{where}-headers takes one site path")
    path = site_path(args[0])
    recorded = blocks(data["headers.txt"])
    if f"{where} {path}" in recorded:
        print("\n".join(recorded[f"{where} {path}"]))
        return 0
    now = dt.datetime(2026, 10, 14, 9, 41, 20, tzinfo=UTC)
    m = None
    if re.fullmatch(r"/summaries/summary-\d{4}-\d\d-\d\d\.json", path):
        m = ls_entry(blocks(data["ls.txt"]), "/srv/www" + path)
    if m is None:
        if where == "cdn":
            print("\n".join(["HTTP/2 404", "content-type: text/html", "content-length: 153",
                             "cache-control: public, max-age=60", f"date: {http_date(now)}", "age: 0",
                             "x-cache: MISS", "x-served-by: edge-ord-4", "via: 1.1 edgecache"]))
        else:
            print("\n".join(["HTTP/1.1 404 Not Found", f"Date: {http_date(now + dt.timedelta(seconds=1))}",
                             "Content-Type: text/html", "Content-Length: 153", "Connection: keep-alive"]))
        return 0
    mtime = dt.datetime.strptime(m["when"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    size = int(m["size"])
    etag = f'"{int(mtime.timestamp()):x}-{size:x}"'
    if where == "cdn":
        hit = h("hit", path) < 0.7
        age = int(h("age", path) * 290) if hit else 0
        print("\n".join(["HTTP/2 200", "content-type: application/json", f"content-length: {size}",
                         f"last-modified: {http_date(mtime)}", f"etag: {etag}", "cache-control: public, max-age=300",
                         "accept-ranges: bytes", f"date: {http_date(now)}", f"age: {age}",
                         f"x-cache: {'HIT' if hit else 'MISS'}", "x-served-by: edge-ord-4", "via: 1.1 edgecache"]))
    else:
        print("\n".join(["HTTP/1.1 200 OK", f"Date: {http_date(now + dt.timedelta(seconds=1))}",
                         "Content-Type: application/json", f"Content-Length: {size}",
                         f"Last-Modified: {http_date(mtime)}", "Connection: keep-alive", f"ETag: {etag}",
                         "Cache-Control: public, max-age=300", "Accept-Ranges: bytes"]))
    return 0


CHECKS = {
    "status": check_status,
    "logs": check_logs,
    "journal": check_journal,
    "timers": check_timers,
    "stat": check_stat,
    "ls": check_ls,
    "id": check_id,
    "cdn-headers": lambda data, args: headers(data, "cdn", args),
    "origin-headers": lambda data, args: headers(data, "origin", args),
    "deploy-log": check_deploy_log,
}


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        sys.stdout.write(HELP)
        return 0 if argv else 2
    host = None
    if argv[0] == "--host" or argv[0].startswith("--host="):
        if argv[0] == "--host":
            if len(argv) < 2:
                print("probe: --host needs a value", file=sys.stderr)
                return 2
            host, argv = argv[1], argv[2:]
        else:
            host, argv = argv[0].split("=", 1)[1], argv[1:]
        if host not in HOSTS:
            print(f"probe: unknown host {host!r} (hosts: {', '.join(HOSTS)})", file=sys.stderr)
            return 2
    if not argv:
        print("probe: no check given; see ./probe --help", file=sys.stderr)
        return 2
    check, args = argv[0], argv[1:]
    if check not in CHECKS:
        print(f"probe: unknown check {check!r}; see ./probe --help", file=sys.stderr)
        return 2
    if host is not None:
        wanted = "cdn" if check == "cdn-headers" else "wx-1"
        if host != wanted:
            print(f"probe: {check} reads {wanted}, not {host}", file=sys.stderr)
            return 2
    if "-h" in args or "--help" in args:
        line = next(l for l in HELP.splitlines() if l.strip().startswith(check + " ") or l.strip() == check)
        print(line.strip())
        return 0
    try:
        return CHECKS[check](load(), args)
    except Usage as exc:
        print(f"probe: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        status = main(sys.argv[1:])
        sys.stdout.flush()
    except BrokenPipeError:
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        status = 1
    sys.exit(status)
