from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).parent.parent / "update_corey_mode.py"
SHA = "5b2c0007766c6a1cf1d53fd8fc73e979e0821022"
BLOB = f"https://github.com/coreyhaines31/marketingskills/blob/{SHA}"
REGENERATE = (
    "; regenerate with: update_corey_mode.py update --upstream DIR --revision SHA"
)
ONE_ROW = "; give each folder in playbooks/ exactly one row in SKILL.md"
ALPHA = """---
name: alpha
description: When the user wants alpha.
---

See [form](references/form.md), [beta](../beta/SKILL.md), [tools](../../tools/REGISTRY.md), [gone](../../gone/SKILL.md), and [web](https://example.com).
"""

ALPHA_RENDERED = f"""---
name: alpha
description: When the user wants alpha.
---

See [form](references/form.md), [beta](../beta/beta.md), [tools]({BLOB}/tools/REGISTRY.md), [gone](../../gone/SKILL.md), and [web](https://example.com).
"""

ROUTES = """# Corey mode

| Route | Use when |
|---|---|
| [`alpha`](playbooks/alpha/alpha.md) | Alpha work |
| [`beta`](playbooks/beta/beta.md) | Beta work |
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )


@pytest.fixture
def upstream(tmp_path: Path) -> Path:
    root = tmp_path / "upstream"
    write(root / "LICENSE", "MIT License\n")
    write(root / "README.md", "# Marketing Skills\n")
    write(root / "tools/REGISTRY.md", "# Registry\n")
    write(root / "skills/alpha/SKILL.md", ALPHA)
    write(
        root / "skills/alpha/references/form.md",
        "Back to [beta](../../beta/SKILL.md#usage).\n",
    )
    write(root / "skills/alpha/evals/evals.json", "{}\n")
    write(root / "skills/beta/SKILL.md", "# Beta\n")
    return root


@pytest.fixture
def package(tmp_path: Path) -> Path:
    root = tmp_path / "corey-mode"
    write(root / "SKILL.md", ROUTES)
    return root


def update(
    upstream: Path, package: Path, *extra: str
) -> subprocess.CompletedProcess[str]:
    return run(
        "update",
        "--upstream",
        str(upstream),
        "--revision",
        SHA,
        "--package",
        str(package),
        *extra,
    )


def files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
    }


def success(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    """The answer of a run that passed: one JSON line on stdout, nothing on stderr."""
    assert (result.returncode, result.stderr) == (0, ""), result.stderr
    assert result.stdout.count("\n") == 1
    return json.loads(result.stdout)


def failure(result: subprocess.CompletedProcess[str], code: int = 1) -> dict[str, Any]:
    """The answer of a run that failed: stdout empty, and stderr one JSON line."""
    assert (result.returncode, result.stdout) == (code, "")
    assert result.stderr.count("\n") == 1, result.stderr
    found = json.loads(result.stderr)
    assert found["ok"] is False
    return found


def test_update_imports_skills_as_playbooks(upstream: Path, package: Path) -> None:
    result = update(upstream, package)

    assert success(result) == {
        "ok": True,
        "changes": [
            ["add", "playbooks/alpha/alpha.md"],
            ["add", "playbooks/alpha/references/form.md"],
            ["add", "playbooks/beta/beta.md"],
            ["add", "references/LICENSE"],
            ["add", "upstream-lock.json"],
        ],
    }
    assert files(package) == {
        "SKILL.md",
        "playbooks/alpha/alpha.md",
        "playbooks/alpha/references/form.md",
        "playbooks/beta/beta.md",
        "references/LICENSE",
        "upstream-lock.json",
    }
    assert (package / "playbooks/alpha/alpha.md").read_text() == ALPHA_RENDERED
    assert (package / "playbooks/alpha/references/form.md").read_text() == (
        "Back to [beta](../../beta/beta.md#usage).\n"
    )
    assert (package / "playbooks/beta/beta.md").read_text() == "# Beta\n"


def test_a_failed_update_answers_the_files_it_already_wrote(
    upstream: Path, package: Path
) -> None:
    (package / "references/LICENSE").mkdir(parents=True)

    answer = failure(update(upstream, package))

    assert answer["changes"] == [
        ["add", "playbooks/alpha/alpha.md"],
        ["add", "playbooks/alpha/references/form.md"],
        ["add", "playbooks/beta/beta.md"],
    ]
    assert answer["errors"][0].startswith("could not write the package: ")


def test_update_rerun_changes_nothing(upstream: Path, package: Path) -> None:
    update(upstream, package)

    result = update(upstream, package)

    assert (result.returncode, result.stdout, result.stderr) == (0, '{"ok":true}\n', "")


def test_dry_run_answers_the_changes_and_writes_nothing(
    upstream: Path, package: Path
) -> None:
    preview = update(upstream, package, "--dry-run")

    assert files(package) == {"SKILL.md"}
    assert success(preview) == success(update(upstream, package))


def test_update_deletes_a_playbook_upstream_removed(
    upstream: Path, package: Path
) -> None:
    update(upstream, package)
    (upstream / "skills/beta/SKILL.md").unlink()

    result = update(upstream, package)

    assert success(result)["changes"] == [
        ["delete", "playbooks/beta/beta.md"],
        ["update", "playbooks/alpha/alpha.md"],
        ["update", "playbooks/alpha/references/form.md"],
        ["update", "upstream-lock.json"],
    ]
    assert not (package / "playbooks/beta").exists()
    assert (
        "[beta](../beta/SKILL.md)" in (package / "playbooks/alpha/alpha.md").read_text()
    )


def test_check_passes_on_a_fresh_import(upstream: Path, package: Path) -> None:
    update(upstream, package)

    result = run("check", "--package", str(package), "--upstream", str(upstream))

    assert (result.returncode, result.stdout, result.stderr) == (0, '{"ok":true}\n', "")


def test_check_reports_hand_edits_and_extra_files(
    upstream: Path, package: Path
) -> None:
    update(upstream, package)
    write(package / "playbooks/alpha/alpha.md", "edited\n")
    write(package / "playbooks/alpha/notes.md", "extra\n")
    write(package / "playbooks/beta/SKILL.md", "---\nname: beta\n---\n")

    result = run("check", "--package", str(package))

    assert failure(result)["errors"] == [
        "changed: playbooks/alpha/alpha.md" + REGENERATE,
        "not in the lock: playbooks/alpha/notes.md" + REGENERATE,
        "not in the lock: playbooks/beta/SKILL.md" + REGENERATE,
        "nested SKILL.md: playbooks/beta/SKILL.md" + REGENERATE,
    ]


def test_check_requires_one_route_per_playbook(upstream: Path, package: Path) -> None:
    update(upstream, package)
    write(
        package / "SKILL.md",
        ROUTES.replace("playbooks/beta/beta.md", "playbooks/beta.md").replace(
            "| [`alpha`](playbooks/alpha/alpha.md) | Alpha work |\n", ""
        )
        + "| [`gamma`](playbooks/gamma/gamma.md) | Gamma work |\n"
        + "| [`gamma`](playbooks/gamma/gamma.md) | Gamma again |\n",
    )

    result = run("check", "--package", str(package))

    assert failure(result)["errors"] == [
        "duplicate route: gamma" + ONE_ROW,
        "route beta links to playbooks/beta.md, not playbooks/beta/beta.md" + ONE_ROW,
        "route without a playbook: gamma" + ONE_ROW,
        "playbook without a route: alpha" + ONE_ROW,
        "broken link in SKILL.md: playbooks/beta.md",
        "broken link in SKILL.md: playbooks/gamma/gamma.md",
        "broken link in SKILL.md: playbooks/gamma/gamma.md",
    ]


def test_check_with_upstream_reports_a_stale_import(
    upstream: Path, package: Path
) -> None:
    update(upstream, package)
    write(upstream / "skills/beta/SKILL.md", "# Beta, revised\n")

    result = run("check", "--package", str(package), "--upstream", str(upstream))

    assert failure(result)["errors"] == [
        f"upstream-lock.json differs from a fresh render of {upstream}" + REGENERATE,
        "differs from upstream: playbooks/beta/beta.md" + REGENERATE,
    ]


def test_a_folder_that_is_not_upstream_fails_with_the_fix(
    tmp_path: Path, package: Path
) -> None:
    result = update(tmp_path / "empty", package)

    assert failure(result)["errors"] == [
        (
            f"{tmp_path / 'empty'} is not a marketingskills checkout: it needs "
            "skills/ and LICENSE; pass --upstream the snapshot folder, such as "
            "$OPENSRC_HOME/repos/github.com/coreyhaines31/marketingskills/main"
        )
    ]
    assert files(package) == {"SKILL.md"}


def test_a_short_revision_is_a_usage_error(upstream: Path, package: Path) -> None:
    result = run(
        "update",
        "--upstream",
        str(upstream),
        "--revision",
        "5b2c000",
        "--package",
        str(package),
    )

    assert failure(result, code=2) == {
        "ok": False,
        "errors": [
            "argument --revision: must be a full 40-character SHA, got '5b2c000'"
        ],
        "help": "update_corey_mode.py update --help",
    }
    assert files(package) == {"SKILL.md"}


def test_update_without_revision_is_a_usage_error(upstream: Path) -> None:
    result = run("update", "--upstream", str(upstream))

    assert failure(result, code=2) == {
        "ok": False,
        "errors": ["the following arguments are required: --revision"],
        "help": "update_corey_mode.py update --help",
    }


def test_an_unknown_flag_is_a_usage_error() -> None:
    result = run("check", "--typo")

    assert failure(result, code=2) == {
        "ok": False,
        "errors": ["unrecognized arguments: --typo"],
        "help": "update_corey_mode.py check --help",
    }


def test_a_command_help_stays_text_and_lists_its_options() -> None:
    result = run("update", "--revision", "short", "--help")

    assert (result.returncode, result.stderr) == (0, "")
    assert result.stdout.startswith("usage: update_corey_mode.py update ")
    assert "--revision REVISION" in result.stdout
    assert "\n  130  interrupted (SIGINT)\n" in result.stdout


def test_verbose_adds_steps_on_stderr_only(upstream: Path, package: Path) -> None:
    update(upstream, package)

    result = run("-v", "check", "--package", str(package))

    assert (result.returncode, result.stdout) == (0, '{"ok":true}\n')
    assert result.stderr == "checked 4 generated files against the lock\n"


@pytest.mark.parametrize(
    "damage",
    [
        "{",
        "null",
        "[]",
        {"schema_version": 2},
        {"repository": "https://example.com/other"},
        {"revision": "5b2c000"},
        {"files": []},
        {"files": {"playbooks/alpha/alpha.md": None}},
        {
            "files": {
                "playbooks/alpha/alpha.md": {
                    "source": "skills/alpha/SKILL.md",
                    "sha256": "bad",
                }
            }
        },
    ],
)
def test_invalid_lock_stops_update_without_writes(
    upstream: Path, package: Path, damage: str | dict[str, object]
) -> None:
    update(upstream, package)
    if isinstance(damage, dict):
        lock = json.loads((package / "upstream-lock.json").read_text(encoding="utf-8"))
        lock.update(damage)
        document = json.dumps(lock)
    else:
        document = damage
    write(package / "upstream-lock.json", document)
    before = {name: (package / name).read_bytes() for name in files(package)}

    result = update(upstream, package)

    [error] = failure(result)["errors"]
    assert error.startswith(f"{package / 'upstream-lock.json'}: invalid lock: ")
    assert error.endswith(
        "; restore a valid upstream-lock.json, then run: "
        f"update_corey_mode.py check --package {package}"
    )
    assert {name: (package / name).read_bytes() for name in files(package)} == before


@pytest.mark.parametrize(
    ("dest", "source"),
    [
        ("SKILL.md", "skills/alpha/SKILL.md"),
        ("../outside.md", "skills/alpha/SKILL.md"),
        ("absolute", "skills/alpha/SKILL.md"),
        ("playbooks/alpha/../alpha/alpha.md", "skills/alpha/SKILL.md"),
        ("playbooks/../../outside.md", "skills/../../outside.md"),
    ],
)
def test_lock_cannot_claim_paths_outside_generated_files(
    upstream: Path, package: Path, dest: str, source: str
) -> None:
    update(upstream, package)
    outside = package.parent / "outside.md"
    write(outside, "handwritten outside the package\n")
    if dest == "absolute":
        dest = str(outside)
    lock = json.loads((package / "upstream-lock.json").read_text(encoding="utf-8"))
    entry = lock["files"].pop("playbooks/alpha/alpha.md")
    lock["files"][dest] = {**entry, "source": source}
    write(package / "upstream-lock.json", json.dumps(lock))
    before = {name: (package / name).read_bytes() for name in files(package)}

    result = update(upstream, package)

    [error] = failure(result)["errors"]
    assert "invalid lock" in error
    assert {name: (package / name).read_bytes() for name in files(package)} == before
    assert outside.read_text(encoding="utf-8") == "handwritten outside the package\n"


def test_missing_handwritten_file_is_a_clean_failure(
    upstream: Path, package: Path
) -> None:
    update(upstream, package)
    (package / "SKILL.md").unlink()

    result = run("check", "--package", str(package))

    assert "SKILL.md" in failure(result)["errors"][0]
