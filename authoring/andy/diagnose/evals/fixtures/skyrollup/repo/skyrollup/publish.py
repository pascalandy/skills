"""Write the day's summary and point the latest link at it."""
import json
import logging
import os

log = logging.getLogger(__name__)


def publish(cfg, summary):
    name = f"summary-{summary['day']}.json"
    path = cfg.summaries_dir / name
    log.info("publishing %s", name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, sort_keys=True)
        f.write("\n")
    tmp = cfg.summaries_dir / f".{cfg.latest_name}.tmp"
    if os.path.lexists(tmp):
        os.unlink(tmp)
    os.symlink(name, tmp)
    os.replace(tmp, cfg.summaries_dir / cfg.latest_name)
    log.info("%s -> %s", cfg.latest_name, name)
    return path
