"""Check identity, reuse, cleanliness, and the offline preview."""

from __future__ import annotations

from jevtest import Project, add_sub, kinds

CHECK = 'echo ran >> "$JEVTEST_HOME/check.log"; exit $(cat "$JEVTEST_HOME/check.exit" 2>/dev/null || echo 0)'


def test_preview_is_offline(project: Project) -> None:
    add_sub(project)
    result = project.jev("run", "merge", "--dry-run", "--run-ci", "--json", key=False)
    assert result.code == 0, result
    assert result.json["check"]["status"] == "unknown"
    assert project.check_runs() == 0
    assert project.records() == []
    assert project.fake.requests == [] and project.fake.model_requests == 0
    assert not project.gh_log.exists()
    payload = project.root / result.json["payload"]
    assert payload.is_file()
    assert project.git("check-ignore", str(payload.relative_to(project.root))) != ""
    assert project.git("status", "--porcelain") == ""
    totals = result.json["totals"]
    assert totals["requests"] == 2 and totals["tokens"] > 0 and totals["bytes"] > 0
    human = project.jev("run", "merge", "--dry-run", "--run-ci", key=False)
    assert human.code == 0
    assert "check: unknown (dry-run never runs or imports checks" in human.stdout
    assert "payload: .jev/runs/preview/" in human.stdout
    assert project.records() == [] and project.check_runs() == 0


def test_check_revision_identity(project: Project) -> None:
    add_sub(project)
    dirty_states = {
        "untracked": lambda: project.write("notes.txt", "draft\n"),
        "unstaged": lambda: project.write(
            "src/calc.py", "def add(a, b):\n    return b + a\n"
        ),
        "staged": lambda: (
            project.write("docs/guide.md", "# Guide\n"),
            project.git("add", "docs/guide.md"),
        ),
    }
    for name, make_dirty in dirty_states.items():
        make_dirty()
        result = project.jev("run", "merge", "--run-ci", "--json")
        assert result.code == 12, (name, result)
        assert kinds(result) == ["dirty_tree"], name
        project.git("reset", "-q", "--hard")
        project.git("clean", "-qfd")
    assert project.check_runs() == 0
    assert project.fake.requests == []

    parent = project.git("rev-parse", "HEAD~1")
    stale = project.jev(
        "run", "merge", "--ci-status", "pass", "--ci-sha", parent, "--json"
    )
    assert stale.code == 12 and kinds(stale) == ["check_stale"]
    assert project.fake.requests == []

    dirtying = {"JEVGATE_CHECK_COMMAND": "echo generated > leftover.txt; " + CHECK}
    first = project.jev("run", "merge", "--run-ci", "--json", env=dirtying)
    assert first.code == 12 and kinds(first) == ["check_dirtied_tree"], first
    (project.root / "leftover.txt").unlink()
    again = project.jev("run", "merge", "--run-ci", "--json", env=dirtying)
    assert again.code == 12 and project.check_runs() == 2, (
        "a check that dirtied the tree is never reused"
    )
    (project.root / "leftover.txt").unlink()
    assert project.fake.requests == []

    green = project.jev("run", "merge", "--run-ci", "--json")
    assert green.code == 0 and project.check_runs() == 3
    changed_command = project.jev(
        "run",
        "merge",
        "--run-ci",
        "--json",
        env={"JEVGATE_CHECK_COMMAND": CHECK + " # variant"},
    )
    assert (
        changed_command.code == 0 and changed_command.json["check"]["reused"] is False
    )
    assert project.check_runs() == 4
    project.commit(
        "Explain sub",
        {"docs/guide.md": "# Guide\n\nThe calculator adds and subtracts.\n"},
    )
    moved = project.jev("run", "merge", "--run-ci", "--json")
    assert moved.code == 0 and moved.json["check"]["reused"] is False
    assert moved.json["check"]["sha"] == project.head()
    assert project.check_runs() == 5


def test_check_reuse(project: Project) -> None:
    head = add_sub(project)
    first = project.jev("run", "merge", "--run-ci", "--json")
    assert first.code == 0, first
    assert first.json["check"]["reused"] is False and project.check_runs() == 1
    second = project.jev("run", "merge", "--run-ci", "--json")
    assert second.code == 0, second
    check = second.json["check"]
    assert check["reused"] is True and project.check_runs() == 1
    assert check["sha"] == head and check["exit"] == 0 and check["command"] == CHECK
    assert isinstance(check["duration_s"], float)
    human = project.jev("run", "merge", "--run-ci")
    assert "check: green, " in human.stderr and "(reused)" in human.stderr


def test_pr_text_sources(project: Project) -> None:
    add_sub(project)
    missing = project.run_merge("--pr", "41")
    assert missing.code == 12, missing
    assert kinds(missing) == ["pr_lookup_failed"]
    assert "could not read pull request #41" in missing.json["reasons"][0]["message"]
    assert project.fake.requests == []

    detected = project.run_merge()
    assert detected.json["claims_source"] == {
        "kind": "commit_messages",
        "count": 1,
        "note": "no pull requests found for branch",
    }

    project.set_pr(41, "Add sub to the calculator", "- Adds sub\n- Tested locally\n")
    live = project.run_merge("--pr", "41")
    assert live.code == 0, live
    source = live.json["claims_source"]
    assert (source["kind"], source["via"], source["number"], source["repository"]) == (
        "pull_request",
        "gh",
        41,
        "example/demo",
    )
    assert source["digest"].startswith("sha256:")
    calls = project.gh_log.read_text().count("pr view")
    (project.home / "pr.json").unlink()
    preview = project.jev("run", "merge", "--dry-run", "--json", key=False)
    assert preview.json["claims"]["source"]["via"] == "saved"
    assert preview.json["claims"]["items"] == {
        "c1": "Add sub to the calculator",
        "c2": "Adds sub",
        "c3": "Tested locally",
    }
    assert project.gh_log.read_text().count("pr view") == calls, (
        "dry-run never calls gh"
    )
