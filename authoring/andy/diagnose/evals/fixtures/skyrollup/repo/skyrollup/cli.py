"""python3 -m skyrollup run|status|logs"""
import argparse
import logging
import sys
import time

from . import __version__, config, job, status

LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
LEVELS = {"debug": 10, "info": 20, "warning": 30, "error": 40}
LINE_LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40, "CRITICAL": 50}


def setup_logging(path):
    logging.addLevelName(logging.WARNING, "WARN")
    formatter = logging.Formatter(LOG_FORMAT)
    formatter.converter = time.gmtime
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(formatter)
    logger = logging.getLogger("skyrollup")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)


def cmd_run(cfg, args):
    setup_logging(cfg.log_file)
    job.run(cfg)
    return 0


def cmd_status(cfg, args):
    print(f"skyrollup {__version__}")
    record = status.read_status(cfg.status_file)
    if record is None:
        print(f"no status file at {cfg.status_file}")
        return 1
    print(f"last_success: {record['last_success']}")
    print(f"result: {record['result']}")
    print(f"day: {record['day']}")
    print(f"stations: {record['stations_reporting']} of {record['stations_expected']}")
    print(f"summary: {record['summary']}")
    return 0


def cmd_logs(cfg, args):
    floor = LEVELS[args.level]
    try:
        lines = cfg.log_file.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        print(f"no log file at {cfg.log_file}", file=sys.stderr)
        return 1
    for line in lines:
        fields = line.split(" ", 3)
        if len(fields) < 4 or fields[2] not in LINE_LEVELS:
            continue
        if args.since and fields[0] < args.since:
            continue
        if LINE_LEVELS[fields[2]] >= floor:
            print(line)
    return 0


COMMANDS = {"run": cmd_run, "status": cmd_status, "logs": cmd_logs}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="skyrollup")
    parser.add_argument("--config", help="config file (default: /etc/skyrollup/config.toml)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="summarize the previous UTC day and publish it")
    sub.add_parser("status", help="show the version and status.json")
    logs = sub.add_parser("logs", help="show lines from the job's log file")
    logs.add_argument("--level", choices=list(LEVELS), default="warning")
    logs.add_argument("--since", metavar="YYYY-MM-DD", help="from this UTC day on")
    args = parser.parse_args(argv)
    cfg = config.load(args.config)
    return COMMANDS[args.command](cfg, args)
