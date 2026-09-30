from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "update_corey_mode.py"
SHA = "5b2c0007766c6a1cf1d53fd8fc73e979e0821022"
BLOB = f"https://github.com/coreyhaines31/marketingskills/blob/{SHA}"
REGENERATE = (
    "regenerate with: update_corey_mode.py update --upstream DIR --revision SHA"
)

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


def test_update_imports_skills_as_playbooks(upstream: Path, package: Path) -> None:
    result = update(upstream, package)

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "add\tplaybooks/alpha/alpha.md",
        "add\tplaybooks/alpha/references/form.md",
        "add\tplaybooks/beta/beta.md",
        "add\treferences/LICENSE",
        "add\tupstream-lock.json",
    ]
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


def test_update_rerun_changes_nothing(upstream: Path, package: Path) -> None:
    update(upstream, package)

    result = update(upstream, package)

    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_dry_run_prints_the_changes_and_writes_nothing(
    upstream: Path, package: Path
) -> None:
    result = update(upstream, package, "--dry-run")

    assert result.returncode == 0
    assert "add\tplaybooks/beta/beta.md" in result.stdout.splitlines()
    assert files(package) == {"SKILL.md"}


def test_update_deletes_a_playbook_upstream_removed(
    upstream: Path, package: Path
) -> None:
    update(upstream, package)
    (upstream / "skills/beta/SKILL.md").unlink()

    result = update(upstream, package)

    assert result.stdout.splitlines() == [
        "delete\tplaybooks/beta/beta.md",
        "update\tplaybooks/alpha/alpha.md",
        "update\tplaybooks/alpha/references/form.md",
        "update\tupstream-lock.json",
    ]
    assert not (package / "playbooks/beta").exists()
    assert (
        "[beta](../beta/SKILL.md)" in (package / "playbooks/alpha/alpha.md").read_text()
    )


def test_check_passes_on_a_fresh_import(upstream: Path, package: Path) -> None:
    update(upstream, package)

    result = run("check", "--package", str(package), "--upstream", str(upstream))

    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_check_reports_hand_edits_and_extra_files(
    upstream: Path, package: Path
) -> None:
    update(upstream, package)
    write(package / "playbooks/alpha/alpha.md", "edited\n")
    write(package / "playbooks/alpha/notes.md", "extra\n")
    write(package / "playbooks/beta/SKILL.md", "---\nname: beta\n---\n")

    result = run("check", "--package", str(package))

    assert result.returncode == 1
    assert result.stderr.splitlines() == [
        "changed: playbooks/alpha/alpha.md",
        "not in the lock: playbooks/alpha/notes.md",
        "not in the lock: playbooks/beta/SKILL.md",
        "nested SKILL.md: playbooks/beta/SKILL.md",
        REGENERATE,
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

    assert result.returncode == 1
    assert result.stderr.splitlines() == [
        "duplicate route: gamma",
        "route beta links to playbooks/beta.md, not playbooks/beta/beta.md",
        "route without a playbook: gamma",
        "playbook without a route: alpha",
        "broken link in SKILL.md: playbooks/beta.md",
        "broken link in SKILL.md: playbooks/gamma/gamma.md",
        "broken link in SKILL.md: playbooks/gamma/gamma.md",
        "give each folder in playbooks/ exactly one row in SKILL.md",
    ]


def test_check_with_upstream_reports_a_stale_import(
    upstream: Path, package: Path
) -> None:
    update(upstream, package)
    write(upstream / "skills/beta/SKILL.md", "# Beta, revised\n")

    result = run("check", "--package", str(package), "--upstream", str(upstream))

    assert result.returncode == 1
    assert result.stderr.splitlines() == [
        "upstream-lock.json differs from a fresh render of " + str(upstream),
        "differs from upstream: playbooks/beta/beta.md",
        REGENERATE,
    ]


def test_update_rejects_a_short_revision(upstream: Path, package: Path) -> None:
    result = run(
        "update",
        "--upstream",
        str(upstream),
        "--revision",
        "5b2c000",
        "--package",
        str(package),
    )

    assert result.returncode == 1
    assert (
        result.stderr == "--revision must be a full 40-character SHA, got '5b2c000'\n"
    )
    assert files(package) == {"SKILL.md"}


def test_update_without_revision_is_a_usage_error(upstream: Path) -> None:
    result = run("update", "--upstream", str(upstream))

    assert result.returncode == 2
    assert result.stderr.splitlines()[-1] == "run 'update_corey_mode.py update --help'"
