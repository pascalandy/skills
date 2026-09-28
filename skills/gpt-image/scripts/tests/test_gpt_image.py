"""Behavior tests for gpt_image.py; no network and no plan usage."""

from __future__ import annotations

import base64
import io
import json
import re
import stat
import urllib.request
from pathlib import Path

import gpt_image
import pytest
from PIL import Image

GUIDE = Path(__file__).parents[2] / "references" / "guide.md"

FAKE_CODEX = """#!/usr/bin/env bash
cat > /dev/null
id="thread-$$-$RANDOM"
mkdir -p "$CODEX_HOME/generated_images/$id"
cp "$FAKE_PNG" "$CODEX_HOME/generated_images/$id/exec-1.png"
printf '{"type":"thread.started","thread_id":"%s"}\\n' "$id"
printf 'TRACE codex_http_client::transport: POST to https://chatgpt.com/backend-api/codex/images/generations: %s\\n' "$FAKE_TRACE_BODY" >&2
"""


def png_bytes(width: int, height: int, mode: str = "RGB") -> bytes:
    buffer = io.BytesIO()
    Image.new(
        mode, (width, height), (200, 30, 30) if mode == "RGB" else (200, 30, 30, 0)
    ).save(buffer, "PNG")
    return buffer.getvalue()


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A machine with no backend until a test adds one."""
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    (tmp_path / "bin").mkdir()
    return tmp_path


@pytest.fixture
def plan_login(env: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Add a logged-in fake Codex that returns a 1254x1254 PNG."""
    home = env / "codex-home"
    home.mkdir()
    (home / "auth.json").write_text(
        json.dumps({"auth_mode": "chatgpt", "tokens": {"access_token": "t"}})
    )
    codex = env / "bin" / "codex"
    codex.write_text(FAKE_CODEX)
    codex.chmod(codex.stat().st_mode | stat.S_IEXEC)
    fake_png = env / "fake.png"
    fake_png.write_bytes(png_bytes(1254, 1254))
    monkeypatch.setenv("FAKE_PNG", str(fake_png))
    monkeypatch.setenv("PATH", f"{env / 'bin'}:/usr/bin:/bin")
    return env


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = gpt_image.main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_fit_size_returns_canonical_sizes() -> None:
    assert gpt_image.fit_size(1.0, 1024 * 1024) == (1024, 1024)
    assert gpt_image.fit_size(1.5, 1536 * 1024) == (1536, 1024)
    assert gpt_image.fit_size(16 / 9, 2560 * 1440) == (2560, 1440)
    assert gpt_image.fit_size(9 / 16, 2560 * 1440) == (1440, 2560)


@pytest.mark.parametrize(
    ("size", "problem"),
    [
        ("1000x1000", "multiples of 16"),
        ("4096x2160", "3840"),
        ("3840x1024", "3 times"),
        ("512x512", "655,360"),
        ("wide", "WIDTHxHEIGHT"),
    ],
)
def test_parse_size_names_the_broken_rule(size: str, problem: str) -> None:
    with pytest.raises(gpt_image.UsageError, match=problem):
        gpt_image.parse_size(size)


def test_output_tokens_match_calculator_estimates() -> None:
    assert gpt_image.output_tokens(1024, 1024, "high") == 1756
    assert gpt_image.output_tokens(1536, 864, "low") == 120
    assert gpt_image.output_tokens(3840, 2160, "max") == 13342
    assert gpt_image.output_tokens(2048, 1152, "xhigh") == 2511


def test_tiers_match_the_guide_tier_table() -> None:
    rows = {
        m.group(1).lower(): (m.group(2).lower(), m.group(3))
        for m in re.finditer(
            r"^\| (Draft|Standard|High|Max) \|[^|]*\| (Flare|Sunburst) \| `(\w+)`",
            GUIDE.read_text(),
            re.MULTILINE,
        )
    }
    assert rows == {
        name: (tier.model, tier.quality) for name, tier in gpt_image.TIERS.items()
    }


def test_no_backend_is_a_usage_error(
    env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, _, err = run(
        capsys, "generate", "--prompt", "a cat", "--out", str(env / "cat.png")
    )
    assert code == 2
    assert "plan backend unavailable" in err


def test_plan_is_the_default_backend_and_max_asks_for_three_candidates(
    plan_login: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = plan_login / "hero.png"
    code, stdout, _ = run(
        capsys,
        "generate",
        "--intent",
        "max",
        "--aspect",
        "16:9",
        "--prompt",
        "A hero",
        "--out",
        str(out),
        "--dry-run",
        "--json",
    )
    receipt = json.loads(stdout)
    assert code == 0
    assert receipt["backend"] == "plan"
    assert receipt["outputs"] == [str(plan_login / f"hero-{i}.png") for i in (1, 2, 3)]
    assert receipt["prompt"] == "A hero\nAspect ratio: 16:9, landscape."


@pytest.mark.parametrize("intent", [None, "draft", "standard", "high", "max"])
def test_openrouter_key_never_changes_the_default_mode(
    plan_login: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    intent: str | None,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    code, stdout, _ = run(
        capsys,
        "generate",
        *(["--intent", intent] if intent else []),
        "--prompt",
        "poster",
        "--out",
        str(plan_login / "out.png"),
        "--dry-run",
        "--json",
    )
    assert code == 0
    receipt = json.loads(stdout)
    assert receipt["backend"] == "plan"
    if intent is None:
        assert receipt["intent"] == "high"
        assert receipt["outputs"] == [str(plan_login / f"out-{i}.png") for i in (1, 2)]


def test_no_plan_does_not_fall_back_to_paid_openrouter(
    env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    code, _, err = run(
        capsys,
        "generate",
        "--prompt",
        "poster",
        "--out",
        str(env / "out.png"),
        "--dry-run",
    )
    assert code == 2
    assert "no paid fallback was selected" in err


@pytest.mark.parametrize("model", ["flare", "sunburst"])
@pytest.mark.parametrize("command", ["generate", "edit"])
def test_explicit_model_uses_openrouter_image_protocol(
    env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    command: str,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    original = png_bytes(1024, 1024)
    source = env / "input.png"
    source.write_bytes(original)
    out = env / "out.png"

    def respond(request: urllib.request.Request, timeout: int) -> io.BytesIO:
        assert request.full_url == "https://openrouter.ai/api/v1/images"
        assert request.get_header("Authorization") == "Bearer sk-test"
        assert request.get_method() == "POST"
        assert isinstance(request.data, bytes)
        expected = {
            "model": f"openai/gpt-image-2.5-{model}",
            "prompt": "poster",
            "quality": "high",
            "background": "auto",
            "output_format": "png",
            "n": 1,
        }
        if command == "edit":
            expected["size"] = "1024x1024"
            expected["input_references"] = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,"
                        + base64.b64encode(original).decode(),
                    },
                }
            ]
        assert json.loads(request.data) == expected
        return io.BytesIO(
            json.dumps(
                {
                    "data": [
                        {
                            "b64_json": base64.b64encode(original).decode(),
                            "media_type": "image/png",
                        }
                    ],
                    "usage": {"cost": 0.013},
                    "size": "1024x1024",
                }
            ).encode()
        )

    monkeypatch.setattr(gpt_image.urllib.request, "urlopen", respond)
    args = [
        command,
        "--model",
        model,
        "--prompt",
        "poster",
        "--out",
        str(out),
        "--json",
    ]
    if command == "edit":
        args += ["--image", str(source)]
    code, stdout, err = run(capsys, *args)
    assert code == 0
    assert err == ""
    receipt = json.loads(stdout)
    assert receipt["backend"] == "openrouter"
    assert receipt["usage"]["cost"] == 0.013
    assert out.read_bytes() == original


def test_explicit_openrouter_defaults_to_high_intent(
    plan_login: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    code, stdout, _ = run(
        capsys,
        "generate",
        "--aspect",
        "3:2",
        "--prompt",
        "A product",
        "--backend",
        "openrouter",
        "--out",
        str(plan_login / "p.png"),
        "--dry-run",
        "--json",
    )
    receipt = json.loads(stdout)
    assert code == 0
    assert receipt["backend"] == "openrouter"
    assert receipt["request"] == {
        "model": "openai/gpt-image-2.5-sunburst",
        "quality": "high",
        "size": "1872x1248",
        "background": "auto",
        "output_format": "png",
        "n": 1,
    }
    assert receipt["estimated_output_tokens"] == gpt_image.output_tokens(
        1872, 1248, "high"
    )


def test_api_only_flags_on_the_plan_backend_are_refused(
    plan_login: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, _, err = run(
        capsys,
        "generate",
        "--backend",
        "plan",
        "--quality",
        "max",
        "--prompt",
        "x",
        "--out",
        str(plan_login / "x.png"),
    )
    assert code == 2
    assert "--quality needs --backend openrouter" in err


def test_transparent_jpeg_is_refused(
    plan_login: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, _, err = run(
        capsys,
        "generate",
        "--transparent",
        "--prompt",
        "x",
        "--out",
        str(plan_login / "x.jpg"),
    )
    assert code == 2
    assert "JPEG has no alpha channel" in err


def test_existing_output_is_kept_without_overwrite(
    plan_login: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = plan_login / "keep.png"
    out.write_bytes(b"old")
    code, _, err = run(
        capsys, "generate", "--candidates", "1", "--prompt", "x", "--out", str(out)
    )
    assert code == 2
    assert "already exists" in err
    assert out.read_bytes() == b"old"


def test_plan_run_writes_the_image_at_the_exact_requested_size(
    plan_login: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "FAKE_TRACE_BODY",
        json.dumps({"prompt": "A banner\nAspect ratio: 16:9, landscape."}),
    )
    out = plan_login / "banner.webp"
    code, stdout, err = run(
        capsys,
        "generate",
        "--candidates",
        "1",
        "--size",
        "1536x864",
        "--prompt",
        "A banner",
        "--out",
        str(out),
        "--json",
    )
    receipt = json.loads(stdout)
    assert code == 0
    assert receipt["calls"][0]["prompt_verbatim"] is True
    assert receipt["files"][0]["width"] == 1536
    assert receipt["files"][0]["height"] == 864
    assert Image.open(out).format == "WEBP"
    assert "upscaled 1254x1254 by 1.22x to reach 1536x864" in err


def test_plan_run_warns_when_codex_changed_the_prompt(
    plan_login: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FAKE_TRACE_BODY", json.dumps({"prompt": "something else"}))
    code, stdout, err = run(
        capsys,
        "generate",
        "--candidates",
        "1",
        "--prompt",
        "A cat",
        "--out",
        str(plan_login / "cat.png"),
    )
    assert code == 0
    assert stdout.startswith("wrote cat.png 1254x1254 via plan in ")
    assert "warning: Codex changed the prompt before sending it" in err


def test_transparent_request_without_alpha_warns(
    plan_login: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FAKE_TRACE_BODY", "{}")
    code, _, err = run(
        capsys,
        "generate",
        "--candidates",
        "1",
        "--transparent",
        "--prompt",
        "A fox",
        "--out",
        str(plan_login / "fox.png"),
    )
    assert code == 0
    assert "fox.png has no alpha channel" in err


def test_alpha_report_reads_a_real_cutout() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    image.paste((255, 0, 0, 254), (25, 25, 75, 75))
    assert gpt_image.alpha_report(image) == {
        "fully_opaque": False,
        "transparent_share": 0.75,
        "near_opaque_share": 0.25,
        "corners_transparent": True,
    }


def test_sent_prompt_reads_the_codex_trace_line() -> None:
    line = (
        "2026-09-28T13:32:43.908904Z TRACE endpoint_session.execute_with{http.method=POST}: "
        "codex_http_client::transport: POST to https://chatgpt.com/backend-api/codex/images/generations: "
        '{"prompt":"A red circle on white.","background":"auto","model":"gpt-image-2","quality":"auto","size":"auto"}'
    )
    assert gpt_image.sent_prompt(f"noise\n{line}\n") == "A red circle on white."


@pytest.mark.parametrize(
    ("input_size", "expected_target", "expected_line"),
    [
        ((1536, 864), "1536x864", "Aspect ratio: 16:9, landscape."),
        ((1000, 750), None, "Aspect ratio: 4:3, landscape."),
    ],
)
def test_edit_keeps_the_first_input_shape(
    plan_login: Path,
    capsys: pytest.CaptureFixture[str],
    input_size: tuple[int, int],
    expected_target: str | None,
    expected_line: str,
) -> None:
    source = plan_login / "source.png"
    source.write_bytes(png_bytes(*input_size))
    code, stdout, _ = run(
        capsys,
        "edit",
        "--image",
        str(source),
        "--prompt",
        "Change only the color.",
        "--out",
        str(plan_login / "edited.png"),
        "--dry-run",
        "--json",
    )
    receipt = json.loads(stdout)
    assert code == 0
    assert receipt.get("target_size") == expected_target
    assert receipt["prompt"] == f"Change only the color.\n{expected_line}"


@pytest.mark.parametrize("format", ["jpeg", "webp", "png"])
def test_api_output_preserves_original_bytes(
    env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    format: str,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    image = Image.effect_noise((128, 128), 70).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format.upper())
    original = buffer.getvalue()
    monkeypatch.setattr(
        gpt_image,
        "api_post",
        lambda route, body: {
            "data": [{"b64_json": base64.b64encode(original).decode()}],
        },
    )
    out = env / f"out.{format}"
    code, _, err = run(
        capsys,
        "generate",
        "--backend",
        "openrouter",
        "--prompt",
        "texture",
        "--out",
        str(out),
    )
    assert code == 0
    assert err == ""
    assert out.read_bytes() == original


def test_api_mismatches_warn_and_list_only_delivered_files(
    env: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    buffer = io.BytesIO()
    Image.new("RGBA", (1024, 1024), (255, 0, 0, 255)).save(buffer, "PNG")
    monkeypatch.setattr(
        gpt_image,
        "api_post",
        lambda route, body: {
            "data": [{"b64_json": base64.b64encode(buffer.getvalue()).decode()}],
            "size": "1024x1024",
            "quality": "low",
            "background": "opaque",
            "output_format": "webp",
        },
    )
    out = env / "out.png"
    code, stdout, err = run(
        capsys,
        "generate",
        "--backend",
        "openrouter",
        "--prompt",
        "sticker",
        "--out",
        str(out),
        "--size",
        "1536x864",
        "--quality",
        "high",
        "--transparent",
        "--candidates",
        "2",
        "--json",
    )
    assert code == 0
    assert "requested 2 images but received 1" in err
    assert "requested quality=high, API reported low" in err
    assert "requested size=1536x864, API reported 1024x1024" in err
    assert "requested background=transparent, API reported opaque" in err
    assert "requested output_format=png, API reported webp" in err
    assert "out-1.png is 1024x1024, requested 1536x864" in err
    assert "out-1.png is fully opaque" in err
    assert json.loads(stdout)["outputs"] == [str(env / "out-1.png")]
    assert not (env / "out-2.png").exists()
