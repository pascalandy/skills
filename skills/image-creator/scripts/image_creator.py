# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=11"]
# ///
"""Generate or edit images with GPT Image through a Codex plan or OpenRouter.

The caller states an intent and a prompt; this CLI owns every other setting.
See ../references/guide.md for the rationale behind each choice.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NoReturn

from PIL import Image

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Settings owned by this CLI

INTENTS = ("draft", "standard", "high", "max")

MODELS = {
    "flare": "openai/gpt-image-2.5-flare",
    "sunburst": "openai/gpt-image-2.5-sunburst",
}
QUALITIES = ("low", "medium", "high", "xhigh", "max")


@dataclass(frozen=True)
class Tier:
    model: str
    quality: str
    pixel_budget: int
    plan_candidates: int


# API settings follow the guide's tier table; the plan backend cannot set model,
# quality, or size, so it spends the higher intents on extra candidates instead.
# The --out extension picks the file format.
TIERS = {
    "draft": Tier("flare", "low", 1024 * 1024, 1),
    "standard": Tier("flare", "medium", 1536 * 1024, 1),
    "high": Tier("sunburst", "high", 2048 * 1152, 2),
    "max": Tier("sunburst", "xhigh", 2560 * 1440, 3),
}

MIN_PIXELS = 655_360
MAX_PIXELS = 8_294_400
MAX_EDGE = 3840
MAX_RATIO = 3.0
EXPERIMENTAL_PIXELS = 2560 * 1440
JPEG_COMPRESSION = 85

API_BASE = "https://openrouter.ai/api/v1"
API_MAX_IMAGES = 16
PLAN_MAX_IMAGES = 5
PLAN_CONTROLLER = "gpt-6-luna"
PLAN_TIMEOUT_S = 300
API_TIMEOUT_S = 600
PLAN_DISABLED_FEATURES = ("computer_use", "browser_use", "in_app_browser")
PLAN_TRACE_MARKER = "POST to https://chatgpt.com/backend-api/codex/images/"

TRANSPARENT_LINE = (
    "Background: fully transparent (real alpha channel). Isolated subject with clean "
    "edges; no backdrop, checkerboard, or shadow."
)


class UsageError(Exception):
    """Bad flags or inputs; exit 2."""


class RunError(Exception):
    """The request could not be completed; exit 1."""


# ---------------------------------------------------------------------------
# Pure helpers


def parse_aspect(text: str) -> float:
    try:
        if ":" in text:
            w, h = (float(part) for part in text.split(":", 1))
            ratio = w / h
        else:
            ratio = float(text)
    except (ValueError, ZeroDivisionError):
        raise UsageError(
            f"--aspect {text!r} is not a ratio; use W:H such as 16:9 or 1:1"
        ) from None
    if not 1 / MAX_RATIO <= ratio <= MAX_RATIO:
        raise UsageError(
            f"--aspect {text} exceeds 3:1; use a ratio between 1:3 and 3:1"
        )
    return ratio


def size_problems(width: int, height: int) -> list[str]:
    problems = []
    if width % 16 or height % 16:
        problems.append("width and height must be multiples of 16")
    if max(width, height) > MAX_EDGE:
        problems.append(f"neither edge may exceed {MAX_EDGE} px")
    if max(width, height) / min(width, height) > MAX_RATIO:
        problems.append("the long edge may be at most 3 times the short edge")
    if not MIN_PIXELS <= width * height <= MAX_PIXELS:
        problems.append(
            f"total pixels must be between {MIN_PIXELS:,} and {MAX_PIXELS:,}"
        )
    return problems


def parse_size(text: str) -> tuple[int, int]:
    try:
        w_text, h_text = text.lower().split("x", 1)
        width, height = int(w_text), int(h_text)
    except ValueError:
        raise UsageError(
            f"--size {text!r} is not WIDTHxHEIGHT; use a value such as 1536x864"
        ) from None
    if width <= 0 or height <= 0:
        raise UsageError(f"--size {text} must use positive dimensions")
    problems = size_problems(width, height)
    if problems:
        raise UsageError(f"--size {text} is invalid: " + "; ".join(problems))
    return width, height


def fit_size(ratio: float, budget: int) -> tuple[int, int]:
    """Return the valid size closest to `budget` pixels whose aspect is within 1% of `ratio`."""
    best: tuple[float, int, int] | None = None
    for height in range(256, MAX_EDGE + 1, 16):
        width = round(ratio * height / 16) * 16
        if width < 16 or size_problems(width, height) or width * height > budget * 1.05:
            continue
        aspect_error = abs(math.log((width / height) / ratio))
        score = (0.0 if aspect_error <= 0.01 else 10.0 + aspect_error) + abs(
            math.log(width * height / budget)
        )
        if best is None or score < best[0]:
            best = (score, width, height)
    if best is None:
        raise UsageError(
            f"no valid size fits aspect {ratio:.3f}; pass --size WIDTHxHEIGHT"
        )
    return best[1], best[2]


def output_tokens(width: int, height: int, quality: str) -> int:
    """Estimate image output tokens using OpenAI's GPT Image 2.5 calculator formula."""
    grid = {"low": 16, "medium": 24, "high": 48, "xhigh": 64, "max": 96}[quality]
    scaled = grid / (max(width, height) / min(width, height))
    floor = math.floor(scaled)
    short = floor + floor % 2 if scaled - floor == 0.5 else round(scaled)
    return math.ceil(grid * short * (2_000_000 + width * height) / 4_000_000)


def candidate_paths(out: Path, count: int) -> list[Path]:
    if count == 1:
        return [out]
    return [out.with_name(f"{out.stem}-{i}{out.suffix}") for i in range(1, count + 1)]


def format_for(path: Path) -> str:
    suffix = path.suffix.lower()
    formats = {".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg", ".webp": "webp"}
    if suffix not in formats:
        raise UsageError(f"--out {path} needs a .png, .jpg, .jpeg, or .webp extension")
    return formats[suffix]


# ---------------------------------------------------------------------------
# Request resolution


@dataclass
class Job:
    command: str
    prompt: str
    intent: str
    out: Path
    aspect: str | None
    size: tuple[int, int] | None
    transparent: bool
    images: list[Path]
    candidates: int | None
    model: str | None
    quality: str | None
    backend: str
    overwrite: bool


@dataclass
class Plan:
    backend: str
    reason: str
    count: int
    paths: list[Path]
    output_format: str
    final_prompt: str
    api_body: dict[str, Any] | None = None
    target_size: tuple[int, int] | None = None
    estimated_output_tokens: int | None = None
    warnings: list[str] = field(default_factory=list)


OPENROUTER_KEYRING = [
    "chezmoi",
    "secret",
    "keyring",
    "get",
    "--service=openrouter",
    "--user=api_key",
]


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def plan_ready() -> tuple[bool, str]:
    if shutil.which("codex") is None:
        return False, "codex is not on PATH"
    auth = codex_home() / "auth.json"
    try:
        data = json.loads(auth.read_text())
    except (OSError, ValueError):
        return False, f"no Codex login at {auth}; run `codex login`"
    if not data.get("tokens"):
        return False, "Codex is not logged in with a ChatGPT plan; run `codex login`"
    return True, "Codex ChatGPT login"


def openrouter_key() -> tuple[str, str]:
    """The OpenRouter key and where it came from, or "" and how to add one.

    The keyring entry comes first; the variable is the fallback for machines
    without chezmoi.
    """
    try:
        found = subprocess.run(
            OPENROUTER_KEYRING, capture_output=True, text=True, timeout=15, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        found = None
    if found is not None and found.returncode == 0 and found.stdout.strip():
        return found.stdout.strip(), "the keyring holds the OpenRouter key"
    if key := os.environ.get("OPENROUTER_API_KEY"):
        return key, "OPENROUTER_API_KEY is set"
    return "", (
        "no OpenRouter key; run `chezmoi secret keyring set --service=openrouter "
        "--user=api_key`, or set OPENROUTER_API_KEY"
    )


def api_ready() -> tuple[bool, str]:
    key, note = openrouter_key()
    return bool(key), note


def choose_backend(job: Job) -> tuple[str, str]:
    if job.backend == "plan" and job.model:
        raise UsageError("--model selects GPT Image 2.5; use --backend openrouter")
    if job.backend == "openrouter" or job.model:
        ready, note = api_ready()
        if not ready:
            raise UsageError(f"OpenRouter backend unavailable: {note}")
        return "openrouter", "explicit GPT Image 2.5 request through OpenRouter"
    if job.quality:
        raise UsageError(
            "--quality needs --backend openrouter or --model; the Codex plan fixes quality"
        )
    ready, note = plan_ready()
    if not ready:
        raise UsageError(
            f"plan backend unavailable: {note}; no paid fallback was selected"
        )
    return "plan", "Codex plan is the default for every intent"


def shape_of(ratio: float) -> str:
    return "landscape" if ratio > 1 else "portrait" if ratio < 1 else "square"


def plan_prompt(job: Job) -> str:
    lines = [job.prompt.strip()]
    if job.size:
        w, h = job.size
        g = math.gcd(w, h)
        lines.append(f"Aspect ratio: {w // g}:{h // g}, {shape_of(w / h)}.")
    elif job.aspect:
        lines.append(
            f"Aspect ratio: {job.aspect}, {shape_of(parse_aspect(job.aspect))}."
        )
    if job.transparent:
        lines.append(TRANSPARENT_LINE)
    return "\n".join(lines)


def resolve(job: Job) -> Plan:
    tier = TIERS[job.intent]
    out_format = format_for(job.out)
    if job.transparent and out_format == "jpeg":
        raise UsageError(
            "--transparent needs a .png or .webp --out; JPEG has no alpha channel"
        )
    backend, reason = choose_backend(job)
    limit = API_MAX_IMAGES if backend == "openrouter" else PLAN_MAX_IMAGES
    if len(job.images) > limit:
        raise UsageError(
            f"{backend} backend accepts at most {limit} --image inputs, got {len(job.images)}"
        )
    count = job.candidates or (tier.plan_candidates if backend == "plan" else 1)
    if not 1 <= count <= 10:
        raise UsageError("--candidates must be between 1 and 10")
    paths = candidate_paths(job.out, count)
    existing = [str(p) for p in paths if p.exists()]
    if existing and not job.overwrite:
        raise UsageError(
            f"{', '.join(existing)} already exists; pass --overwrite or choose another --out"
        )

    if backend == "plan":
        return Plan(
            backend,
            reason,
            count,
            paths,
            out_format,
            plan_prompt(job),
            target_size=job.size,
        )

    if job.size:
        size = job.size
    elif job.aspect:
        size = fit_size(parse_aspect(job.aspect), tier.pixel_budget)
    else:
        size = None
    quality = job.quality or tier.quality
    model = MODELS[job.model] if job.model else MODELS[tier.model]
    api_format = out_format
    body: dict[str, Any] = {
        "model": model,
        "prompt": job.prompt.strip()
        + (f"\n{TRANSPARENT_LINE}" if job.transparent else ""),
        "quality": quality,
        "background": "transparent" if job.transparent else "auto",
        "output_format": api_format,
        "n": count,
    }
    if size:
        body["size"] = f"{size[0]}x{size[1]}"
    if api_format in ("jpeg", "webp"):
        body["output_compression"] = JPEG_COMPRESSION
    plan = Plan(
        backend,
        reason,
        count,
        paths,
        out_format,
        body["prompt"],
        api_body=body,
        target_size=size,
    )
    if size:
        plan.estimated_output_tokens = output_tokens(size[0], size[1], quality) * count
        if size[0] * size[1] > EXPERIMENTAL_PIXELS:
            plan.warnings.append(
                f"{size[0]}x{size[1]} is above 2560x1440, which OpenAI marks experimental"
            )
    return plan


# ---------------------------------------------------------------------------
# Image handling


def describe(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        info: dict[str, Any] = {
            "path": str(path),
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "bytes": path.stat().st_size,
        }
        if image.mode in ("RGBA", "LA"):
            info["alpha"] = alpha_report(image)
    return info


def alpha_report(image: Image.Image) -> dict[str, Any]:
    alpha = image.getchannel("A")
    histogram = alpha.histogram()
    total = image.width * image.height
    corners = [
        alpha.getpixel((0, 0)),
        alpha.getpixel((image.width - 1, 0)),
        alpha.getpixel((0, image.height - 1)),
        alpha.getpixel((image.width - 1, image.height - 1)),
    ]
    return {
        "fully_opaque": histogram[255] == total,
        "transparent_share": round(histogram[0] / total, 4),
        "near_opaque_share": round(sum(histogram[250:]) / total, 4),
        "corners_transparent": all(c == 0 for c in corners),
    }


def save_image(
    data: bytes, dest: Path, out_format: str, target: tuple[int, int] | None
) -> list[str]:
    """Write `data` to `dest` in `out_format`, cropping and resizing to `target` when given."""
    notes = []
    with Image.open(io.BytesIO(data)) as source:
        image = source.copy()
        unchanged = source.format == out_format.upper() and (
            target is None or source.size == target
        )
    if target and image.size != target:
        tw, th = target
        scale = max(tw / image.width, th / image.height)
        if scale > 1:
            notes.append(
                f"upscaled {image.width}x{image.height} by {scale:.2f}x to reach {tw}x{th}"
            )
        crop_w, crop_h = round(tw / scale), round(th / scale)
        left, top = (image.width - crop_w) // 2, (image.height - crop_h) // 2
        image = image.crop((left, top, left + crop_w, top + crop_h)).resize(
            target, Image.Resampling.LANCZOS
        )
    if out_format == "jpeg" and image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".{dest.name}.tmp")
    save_kwargs: dict[str, Any] = (
        {"quality": JPEG_COMPRESSION} if out_format in ("jpeg", "webp") else {}
    )
    if unchanged:
        tmp.write_bytes(data)
    else:
        image.save(tmp, format=out_format.upper(), **save_kwargs)
    tmp.replace(dest)
    return notes


# ---------------------------------------------------------------------------
# Backends


def plan_instruction(prompt: str, images: list[Path]) -> str:
    refs = ""
    if images:
        listed = json.dumps([str(p.resolve()) for p in images])
        refs = f"Set referenced_image_paths to exactly {listed}, in that order. "
    return (
        "Call the image generation tool exactly once. "
        f"{refs}"
        "Pass the prompt between the markers character for character, with no changes, "
        "additions, or reformatting. Do not run shell commands or use any other tool. "
        "After the tool returns, reply DONE.\n"
        f"<<<PROMPT\n{prompt}\nPROMPT>>>\n"
    )


def sent_prompt(stderr: str) -> str | None:
    """Return the prompt Codex sent to the image endpoint, read from its trace log."""
    for line in stderr.splitlines():
        index = line.find(PLAN_TRACE_MARKER)
        if index < 0:
            continue
        body_start = line.find("{", index)
        if body_start < 0:
            continue
        try:
            body = json.loads(line[body_start:])
        except ValueError:
            continue
        if isinstance(body, dict) and isinstance(body.get("prompt"), str):
            return body["prompt"]
    return None


def plan_generate_one(
    prompt: str, images: list[Path], verbose: bool
) -> tuple[bytes, dict[str, Any]]:
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="image-creator-") as work:
        cmd = [
            "codex", "exec", "--ephemeral", "--ignore-user-config", "--skip-git-repo-check",
            "-C", work, "-s", "read-only", "-c", 'approval_policy="never"',
            "-m", PLAN_CONTROLLER, "-c", 'model_reasoning_effort="low"', "--json",
        ]  # fmt: skip
        for feature in PLAN_DISABLED_FEATURES:
            cmd += ["--disable", feature]
        cmd.append("-")
        env = {**os.environ, "RUST_LOG": "codex_http_client::transport=trace"}
        try:
            result = subprocess.run(
                cmd, input=plan_instruction(prompt, images), capture_output=True, text=True,
                timeout=PLAN_TIMEOUT_S, env=env, check=False,
            )  # fmt: skip
        except subprocess.TimeoutExpired:
            raise RunError(
                f"codex exec timed out after {PLAN_TIMEOUT_S} s; retry the plan request"
            ) from None
    thread_id = None
    for line in result.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "thread.started":
            thread_id = event.get("thread_id")
    detail = f"\n{result.stderr[-2000:]}" if verbose else ""
    if result.returncode != 0 or not thread_id:
        raise RunError(
            f"codex exec failed with exit {result.returncode}; run `codex login status`{detail}"
        )
    folder = codex_home() / "generated_images" / thread_id
    produced = (
        sorted(folder.glob("*.png"), key=lambda p: p.stat().st_mtime)
        if folder.is_dir()
        else []
    )
    if not produced:
        raise RunError(
            f"Codex returned no image; the controller may have skipped the tool, retry once{detail}"
        )
    sent = sent_prompt(result.stderr)
    meta = {
        "seconds": round(time.monotonic() - started, 1),
        "source": str(produced[-1]),
        "prompt_verbatim": None if sent is None else sent == prompt,
    }
    return produced[-1].read_bytes(), meta


def plan_run(plan: Plan, job: Job, verbose: bool) -> tuple[list[bytes], dict[str, Any]]:
    with ThreadPoolExecutor(max_workers=plan.count) as pool:
        futures = [
            pool.submit(plan_generate_one, plan.final_prompt, job.images, verbose)
            for _ in range(plan.count)
        ]
        results = [f.result() for f in futures]
    calls = [meta for _, meta in results]
    if any(call["prompt_verbatim"] is False for call in calls):
        plan.warnings.append(
            "Codex changed the prompt before sending it; inspect the result"
        )
    return [data for data, _ in results], {"calls": calls}


def data_url(path: Path) -> str:
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    kind = mime.get(path.suffix.lower())
    if kind is None:
        raise UsageError(f"{path} must be a .png, .jpg, .jpeg, or .webp image")
    return f"data:{kind};base64,{base64.b64encode(path.read_bytes()).decode()}"


def api_post(route: str, body: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{API_BASE}/{route}",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {openrouter_key()[0]}",
            "Content-Type": "application/json",
        },
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=API_TIMEOUT_S) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            payload = error.read().decode(errors="replace")
            if (error.code == 429 or error.code >= 500) and attempt < 2:
                time.sleep(2**attempt * 5)
                continue
            try:
                detail = json.loads(payload).get("error", {})
            except ValueError:
                detail = {"message": payload[:300]}
            code = detail.get("code") or detail.get("type") or error.code
            hint = {
                401: "check the OpenRouter key in the keyring or OPENROUTER_API_KEY",
                402: "check your OpenRouter credit balance",
                403: "check OpenRouter account and provider access",
            }.get(
                error.code,
                "change the prompt or inputs before retrying"
                if error.code == 400
                else "retry later",
            )
            raise RunError(
                f"OpenRouter API {error.code} ({code}): {detail.get('message', '')}; {hint}"
            ) from None
        except urllib.error.URLError as error:
            raise RunError(f"cannot reach the OpenRouter API: {error.reason}") from None
    raise RunError("OpenRouter API kept failing after 3 attempts; retry later")


def api_run(plan: Plan, job: Job) -> tuple[list[bytes], dict[str, Any]]:
    assert plan.api_body is not None
    body = dict(plan.api_body)
    started = time.monotonic()
    if job.command == "edit":
        body["input_references"] = [
            {"type": "image_url", "image_url": {"url": data_url(p)}} for p in job.images
        ]
    response = api_post("images", body)
    images = [
        base64.b64decode(item["b64_json"])
        for item in response.get("data", [])
        if item.get("b64_json")
    ]
    if not images:
        raise RunError("OpenRouter API returned no image data; retry once")
    meta = {
        "seconds": round(time.monotonic() - started, 1),
        "effective": {
            k: response.get(k)
            for k in ("quality", "size", "background", "output_format")
        },
        "usage": response.get("usage"),
    }
    return images, meta


# ---------------------------------------------------------------------------
# Commands


def run_job(job: Job, dry_run: bool, verbose: bool) -> dict[str, Any]:
    plan = resolve(job)
    receipt: dict[str, Any] = {
        "command": job.command,
        "intent": job.intent,
        "backend": plan.backend,
        "backend_reason": plan.reason,
        "candidates": plan.count,
        "outputs": [str(p) for p in plan.paths],
        "prompt": plan.final_prompt,
    }
    if plan.api_body:
        receipt["request"] = {k: v for k, v in plan.api_body.items() if k != "prompt"}
        if plan.estimated_output_tokens is not None:
            receipt["estimated_output_tokens"] = plan.estimated_output_tokens
            receipt["estimated_output_usd"] = round(
                plan.estimated_output_tokens * 30 / 1_000_000, 4
            )
    else:
        receipt["request"] = {
            "controller": PLAN_CONTROLLER,
            "note": "the plan backend fixes model, quality, and size",
        }
    if plan.target_size:
        receipt["target_size"] = f"{plan.target_size[0]}x{plan.target_size[1]}"
    if dry_run:
        receipt["dry_run"] = True
        receipt["warnings"] = plan.warnings
        return receipt

    images, meta = (
        plan_run(plan, job, verbose) if plan.backend == "plan" else api_run(plan, job)
    )
    receipt.update(meta)
    if len(images) != plan.count:
        plan.warnings.append(
            f"requested {plan.count} images but received {len(images)}; inspect the outputs"
        )
    if plan.api_body:
        for key, actual in meta.get("effective", {}).items():
            expected = plan.api_body.get(key)
            if (
                expected not in (None, "auto")
                and actual is not None
                and actual != expected
            ):
                plan.warnings.append(
                    f"requested {key}={expected}, API reported {actual}"
                )
    files = []
    for data, path in zip(images, plan.paths, strict=False):
        target = plan.target_size if plan.backend == "plan" else None
        plan.warnings += save_image(data, path, plan.output_format, target)
        info = describe(path)
        if plan.target_size and (info["width"], info["height"]) != plan.target_size:
            plan.warnings.append(
                f"{path.name} is {info['width']}x{info['height']}, "
                f"requested {plan.target_size[0]}x{plan.target_size[1]}"
            )
        if job.transparent and "alpha" not in info:
            plan.warnings.append(
                f"{path.name} has no alpha channel; retry with a transparent background"
            )
        elif job.transparent and info["alpha"]["fully_opaque"]:
            plan.warnings.append(
                f"{path.name} is fully opaque; retry with a transparent background"
            )
        files.append(info)
    receipt["outputs"] = [f["path"] for f in files]
    receipt["files"] = files
    receipt["warnings"] = plan.warnings
    return receipt


def doctor() -> dict[str, Any]:
    has_plan, plan_note = plan_ready()
    has_api, api_note = api_ready()
    return {
        "plan": {"ready": has_plan, "detail": plan_note},
        "openrouter": {"ready": has_api, "detail": api_note},
    }


# ---------------------------------------------------------------------------
# CLI

INTENT_USE = {
    "draft": "quick idea",
    "standard": "everyday image",
    "high": "client-facing final (default)",
    "max": "quality is paramount",
}

EPILOG_GENERATE = (
    "intents:\n"
    + "".join(
        f"  {name:<9} {INTENT_USE[name]}; plan: {t.plan_candidates} image(s); "
        f"API: {t.model.title()} {t.quality}, ~{t.pixel_budget / 1e6:.1f} MP\n"
        for name, t in TIERS.items()
    )
    + """
backend auto: always the Codex plan, including high and max.
Select GPT Image 2.5 explicitly with --model flare/sunburst or --backend openrouter.
OpenRouter requires OPENROUTER_API_KEY; there is no automatic paid fallback.
The plan fixes model, quality, and size; --size is applied by cropping and resizing.

examples:
  image_creator.py generate --prompt "Minimal poster ..." --out poster.png
  image_creator.py generate --intent max --aspect 16:9 --prompt-file brief.txt --out hero.png --json
  image_creator.py generate --intent draft --out idea.jpg --prompt "Three layout ideas for ..."
  image_creator.py generate --transparent --out logo.png --prompt "Flat vector logo ..."
"""
)

EPILOG_EDIT = """\
examples:
  image_creator.py edit --image photo.png --out photo-snow.png \\
    --prompt "Change only the weather to light snow. Keep the person, pose, and framing unchanged."
  image_creator.py edit --image scene.png --image subject.png --intent high --out combined.png \\
    --prompt "Image 1 is the scene; image 2 is the subject. ..."
"""


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.exit(2, f"error: {message}\nrun with --help for usage\n")


def add_job_options(parser: argparse.ArgumentParser) -> None:
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--prompt", help="image description")
    source.add_argument(
        "--prompt-file", type=Path, help="file holding the prompt; - reads stdin"
    )
    parser.add_argument(
        "--out", required=True, type=Path, help="output file: .png, .jpg, or .webp"
    )
    parser.add_argument(
        "--intent",
        choices=INTENTS,
        default="high",
        help="quality intent (default: high)",
    )
    shape = parser.add_mutually_exclusive_group()
    shape.add_argument("--aspect", help="aspect ratio such as 16:9, 1:1, 2:3")
    shape.add_argument("--size", help="exact WIDTHxHEIGHT, multiples of 16")
    parser.add_argument(
        "--transparent",
        action="store_true",
        help="transparent background (PNG or WebP)",
    )
    parser.add_argument(
        "--candidates",
        type=int,
        help="images to produce (default: set by intent and backend)",
    )
    parser.add_argument(
        "--backend", choices=("auto", "plan", "openrouter"), default="auto"
    )
    parser.add_argument(
        "--model",
        choices=tuple(MODELS),
        help="OpenRouter only: override the intent's model",
    )
    parser.add_argument(
        "--quality",
        choices=QUALITIES,
        help="OpenRouter only: override the intent's quality",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="replace existing output files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the resolved request; make no call",
    )
    parser.add_argument(
        "--json", action="store_true", help="print the full receipt as JSON"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="details and Codex logs on failure"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = Parser(
        prog="image_creator.py",
        description="Generate or edit images with GPT Image through a ChatGPT plan or the OpenRouter API.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    generate = sub.add_parser(
        "generate", help="create a new image", epilog=EPILOG_GENERATE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )  # fmt: skip
    add_job_options(generate)
    edit = sub.add_parser(
        "edit", help="edit or combine input images", epilog=EPILOG_EDIT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )  # fmt: skip
    edit.add_argument(
        "--image",
        action="append",
        required=True,
        type=Path,
        help="input image; repeat, order matters",
    )
    add_job_options(edit)
    check = sub.add_parser("doctor", help="report which backends are ready")
    check.add_argument("--json", action="store_true", help="print JSON")
    return parser


def edit_shape(path: Path) -> tuple[tuple[int, int] | None, str | None]:
    """An edit keeps its first input's size, or its aspect when the size is invalid."""
    try:
        with Image.open(path) as image:
            width, height = image.size
    except OSError:
        raise UsageError(f"input image {path} is not a readable image") from None
    if not size_problems(width, height):
        return (width, height), None
    if 1 / MAX_RATIO <= width / height <= MAX_RATIO:
        g = math.gcd(width, height)
        return None, f"{width // g}:{height // g}"
    return None, None


def job_from_args(args: argparse.Namespace) -> Job:
    if args.prompt is not None:
        prompt = args.prompt
    elif str(args.prompt_file) == "-":
        prompt = sys.stdin.read()
    else:
        try:
            prompt = args.prompt_file.read_text()
        except OSError as error:
            raise UsageError(
                f"cannot read --prompt-file {args.prompt_file}: {error.strerror}"
            ) from None
    if not prompt.strip():
        raise UsageError("the prompt is empty")
    aspect = args.aspect
    if aspect:
        parse_aspect(aspect)
    size = parse_size(args.size) if args.size else None
    images = list(getattr(args, "image", None) or [])
    for path in images:
        if not path.is_file():
            raise UsageError(f"input image {path} does not exist")
    if images and not (size or aspect):
        size, aspect = edit_shape(images[0])
    return Job(
        command=args.command,
        prompt=prompt,
        intent=args.intent,
        out=args.out,
        aspect=aspect,
        size=size,
        transparent=args.transparent,
        images=images,
        candidates=args.candidates,
        model=args.model,
        quality=args.quality,
        backend=args.backend,
        overwrite=args.overwrite,
    )


def summary_line(receipt: dict[str, Any]) -> str:
    if receipt.get("dry_run"):
        return f"dry run: {receipt['backend']} backend would write {' '.join(receipt['outputs'])}"
    files = receipt["files"]
    sizes = ", ".join(
        f"{Path(f['path']).name} {f['width']}x{f['height']}" for f in files
    )
    seconds = receipt.get("seconds") or max(
        (c["seconds"] for c in receipt.get("calls", [])), default=0
    )
    return f"wrote {sizes} via {receipt['backend']} in {seconds}s"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    verbose = getattr(args, "verbose", False)
    try:
        if args.command == "doctor":
            report = doctor()
            if args.json:
                print(json.dumps(report))
            else:
                print(
                    "; ".join(
                        f"{name}: {'ready' if r['ready'] else 'missing'} ({r['detail']})"
                        for name, r in report.items()
                    )
                )
            return 0 if any(r["ready"] for r in report.values()) else 1
        receipt = run_job(job_from_args(args), args.dry_run, verbose)
    except UsageError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except RunError as error:
        print(f"error: {error}", file=sys.stderr)
        if not verbose:
            print("rerun with --verbose for details", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    for warning in receipt.get("warnings", []):
        print(f"warning: {warning}", file=sys.stderr)
    print(json.dumps(receipt, indent=2) if args.json else summary_line(receipt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
