"""What may leave the machine: deny globs, ignored files, the secret scan, and test evidence.

Planted secrets are assembled at runtime so no token-shaped literal is committed.
"""

from __future__ import annotations

import json
from pathlib import Path

from jevtest import FakeTypeSafe, Project, add_sub, kinds, make_project

SUB = "def add(a, b):\n    return a + b\n\n\ndef sub(a, b):\n    return a - b\n"


def on_main(
    project: Project, message: str, files: dict[str, str], force: tuple[str, ...] = ()
) -> None:
    project.git("checkout", "-q", "main")
    project.commit(message, files, force=force)  # type: ignore[arg-type]
    project.git("checkout", "-q", "feature")
    project.git("reset", "-q", "--hard", "main")


def test_payload_filters(project: Project) -> None:
    on_main(
        project,
        "Add sample settings",
        {"config/.env.sample": "OLD-DENIED-MARKER=1\n", "notes/keep.md": "# Notes\n"},
    )
    project.edit_config("deny_globs = []", 'deny_globs = ["private/**"]')
    project.git("mv", "config/.env.sample", "config/sample.conf")
    project.git("mv", "docs/guide.md", "docs/.env.guide")
    project.commit(
        "Add denied, ignored, and ordinary files",
        {
            "src/calc.py": SUB,
            "keys/server.pem": "DENIED-PEM-MARKER\n",
            "private/plan.md": "DENIED-PROJECT-MARKER\n",
            "src/secrets/notes.txt": "DENIED-SECRETS-DIR-MARKER\n",
            "local/cache.txt": "IGNORED-DIR-MARKER\n",
            "src/debug.log": "IGNORED-TRACKED-MARKER\n",
            "notes/keep.md": "# Notes\n\nOrdinary text.\n",
        },
        force=("local/cache.txt", "src/debug.log"),
    )
    markers = [
        "OLD-DENIED-MARKER",
        "DENIED-PEM-MARKER",
        "DENIED-PROJECT-MARKER",
        "DENIED-SECRETS-DIR-MARKER",
        "IGNORED-DIR-MARKER",
        "IGNORED-TRACKED-MARKER",
        "The calculator adds numbers",
    ]

    preview = project.jev("run", "merge", "--dry-run", "--json", key=False)
    assert preview.code == 0, preview
    payload = (project.root / preview.json["payload"]).read_text()
    omitted = {item["path"]: item["why"] for item in preview.json["omitted"]}
    assert omitted == {
        "config/sample.conf": "deny glob .env.*",
        "docs/.env.guide": "deny glob .env.*",
        "keys/server.pem": "deny glob *.pem",
        "private/plan.md": "deny glob private/**",
        "src/secrets/notes.txt": "deny glob **/secrets/**",
        "local/cache.txt": "ignored by git",
        "src/debug.log": "ignored by git",
        ".jev/config.toml": "jevgate data",
    }
    assert "notes/keep.md" in payload

    live = project.run_merge()
    sent = json.dumps(project.fake.requests)
    for marker in markers:
        assert marker not in payload, marker
        assert marker not in sent, marker
    assert live.code == 10, live
    unjudged = {
        reason["scope"]
        for reason in live.json["reasons"]
        if reason["kind"] == "unjudged"
    }
    assert unjudged == {
        "group:config",
        "group:docs",
        "group:keys",
        "group:local",
        "group:private",
        "group:src",
        "group:src/secrets",
    }
    assert "notes" in project.fake.groups_asked()


def test_secret_blocks_before_transport(tmp_path: Path, fake: FakeTypeSafe) -> None:
    token = "ghp_" + "Ab1" * 12
    project = make_project(tmp_path / "code", fake)
    add_sub(project)
    project.commit(
        "Read the service token", {"src/settings.py": f'TOKEN = "{token}"\n'}
    )
    result = project.run_merge()
    assert result.code == 11, result
    assert set(kinds(result)) == {"secret_in_payload"}
    assert fake.requests == []
    record = (project.root / result.json["record"]).read_text()
    for text in (result.stdout, result.stderr, record):
        assert token not in text
    assert "src/settings.py@@1" in result.json["reasons"][0]["message"]
    preview = project.jev("run", "merge", "--dry-run", "--json", key=False)
    assert preview.code == 11 and preview.json["payload"] is None
    assert not (project.root / ".jev" / "runs" / "preview").exists()

    key = "AKIA" + "QW3RTY7UI0PA5SDF"
    author = make_project(tmp_path / "author", fake)
    add_sub(author, f"Add sub\n\nStaging deploy uses {key} for now")
    result = author.run_merge()
    assert result.code == 11, result
    assert fake.requests == []
    assert "author_text" in result.json["reasons"][0]["message"]
    assert (
        key
        not in result.stdout
        + result.stderr
        + (author.root / result.json["record"]).read_text()
    )


def test_existing_test_evidence(project: Project) -> None:
    on_main(
        project,
        "Add fixtures",
        {
            "tests/secrets/test_calc.py": "DENIED-TEST-MARKER = 1\n",
            "tests/calc_test.log": "IGNORED-TEST-MARKER\n",
        },
        force=("tests/calc_test.log",),
    )
    project.commit(
        "Add sub",
        {
            "src/calc.py": SUB,
            "lib/util.py": "def clamp(value):\n    return max(0, value)\n",
        },
    )
    preview = project.jev("run", "merge", "--dry-run", "--json", key=False)
    groups = {group["name"]: group for group in preview.json["groups"]}
    assert groups["src"]["existing_tests"] == ["tests/test_calc.py"]
    assert groups["lib"]["existing_tests"] == []
    payload = (project.root / preview.json["payload"]).read_text()
    assert "def test_add" in payload
    assert "DENIED-TEST-MARKER" not in payload and "IGNORED-TEST-MARKER" not in payload
    assert preview.json["missing_proof"] == [
        {
            "group": "lib",
            "kind": "test_evidence",
            "why": "no changed or existing test matches its code files",
        }
    ]

    live = project.run_merge()
    assert live.code == 0, live
    record = json.loads((project.root / live.json["record"]).read_text())
    selection = {item["path"]: item for item in record["evidence"]["selection"]}
    assert selection["tests/test_calc.py"]["selected"] is True
    assert selection["tests/secrets/test_calc.py"] == {
        "group": "src",
        "path": "tests/secrets/test_calc.py",
        "selected": False,
        "why": "deny glob **/secrets/**",
    }
    assert selection["tests/calc_test.log"]["why"] == "ignored by git"
    assert record["evidence"]["missing_proof"][0]["group"] == "lib"

    project.edit_config("existing_test_bytes = 12000", "existing_test_bytes = 20")
    small = project.jev("run", "merge", "--dry-run", "--json", key=False)
    body = json.loads((project.root / small.json["payload"]).read_text())
    src = next(request for request in body["requests"] if request["id"] == "group:src")
    assert src["body"]["state"]["existing_tests"][0]["truncated"] is True

    project.edit(
        ".jev/packs/merge.toml",
        'id = "merge"\n',
        'id = "merge"\nrequires = ["test_evidence"]\n',
    )
    sent = len(project.fake.requests)
    required = project.run_merge()
    assert required.code == 12, required
    assert kinds(required) == ["required_proof_missing"]
    assert len(project.fake.requests) == sent
