import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PATH = "/etc/skyrollup/config.toml"


@dataclass(frozen=True)
class Config:
    source_url: str
    timeout: float
    stations: tuple
    summaries_dir: Path
    latest_name: str
    status_file: Path
    log_file: Path


def load(path=None):
    path = path or os.environ.get("SKYROLLUP_CONFIG") or DEFAULT_PATH
    with open(path, "rb") as f:
        data = tomllib.load(f)
    source, output, state = data["source"], data["output"], data["state"]
    return Config(
        source_url=source["url"].rstrip("/"),
        timeout=float(source.get("timeout", 20)),
        stations=tuple(source["stations"]),
        summaries_dir=Path(output["summaries_dir"]),
        latest_name=output.get("latest", "summary-latest.json"),
        status_file=Path(state["status_file"]),
        log_file=Path(state["log_file"]),
    )
