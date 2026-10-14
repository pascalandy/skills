"""python3 -m skyrollup run|status"""
import argparse
import logging
import time

from . import __version__, config, job, status

LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"


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


COMMANDS = {"run": cmd_run, "status": cmd_status}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="skyrollup")
    parser.add_argument("--config", help="config file (default: /etc/skyrollup/config.toml)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="summarize the previous UTC day and publish it")
    sub.add_parser("status", help="show the version and status.json")
    args = parser.parse_args(argv)
    cfg = config.load(args.config)
    return COMMANDS[args.command](cfg, args)
