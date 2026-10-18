"""Synthetic replay output and the command's public CLI boundary."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "replay.py"


@pytest.fixture
def replay(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    monkeypatch.syspath_prepend(str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("brigade_replay_command", SCRIPT)
    assert spec and spec.loader
    command = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(command)
    return command


def fact(second: int, role: str, thread: str, kind: str, **fields: object) -> dict:
    import facts

    event: dict[str, object] = {key: None for key in facts.KEYS}
    event.update(
        time=f"2026-01-01T00:00:{second:02d}.000Z",
        brigade="abcd",
        role=role,
        thread=thread,
        kind=kind,
    )
    event.update(fields)
    return event


@pytest.mark.parametrize(
    "repo", ["example-owner/confidential-widget", "example-owner/replay"]
)
def test_private_run_keeps_epic_cook_and_story_count(
    tmp_path: Path, replay: ModuleType, repo: str
) -> None:
    events = [
        fact(0, "pascal", "hc", "pascal_msg", detail={"intent": "reply"}),
        fact(
            1,
            "head_chef",
            "hc",
            "batch_register",
            detail={"batch": 1, "name": "Synthetic batch"},
        ),
        fact(
            2,
            "chef",
            "chef-1",
            "launch",
            parent="hc",
            detail={"label": "Chef 1", "repo": repo, "release": False},
        ),
        fact(
            3,
            "cook",
            "cook-1.1",
            "launch",
            parent="chef-1",
            detail={"label": "Cook 1.1", "repo": repo},
        ),
        fact(4, "cook", "cook-1.1", "run_start", detail={"run": "1"}),
        fact(
            5,
            "github",
            "chef-1",
            "story_scope",
            epic=repo + "#9",
            story=repo + "#10",
            detail={"batch": 1, "state_at_scope": "open"},
        ),
        fact(
            6,
            "github",
            "cook-1.1",
            "pr_open",
            epic=repo + "#9",
            story=repo + "#10",
            pr=repo + "#20",
        ),
        fact(
            7,
            "github",
            "cook-1.1",
            "pr_open",
            epic=repo + "#9",
            story=repo + "#11",
            pr=repo + "#21",
        ),
        fact(9, "cook", "cook-1.1", "run_end", detail={"run": "1"}),
        fact(
            10,
            "cook",
            "cook-1.1",
            "send",
            detail={"to": "chef-1", "msg": "stack_ready", "checks": "pass"},
        ),
        fact(11, "head_chef", "hc", "ask_pascal", detail={"items": ["merge"]}),
        fact(12, "chef", "chef-1", "send", detail={"to": "hc", "msg": "question"}),
    ]
    public, names = replay.repository_names({repo: {"visibility": "PRIVATE"}})
    data = replay.board.build(events, public, {repo + "#9": 3}, names)
    output = tmp_path / "replay.html"
    output.write_text(replay.render_page(data, {repo: names[repo]}), encoding="utf-8")
    page = output.read_text(encoding="utf-8")
    match = re.search(r"\bconst\s+DATA\s*=\s*", page)
    assert match
    embedded, _ = json.JSONDecoder().raw_decode(page[match.end() :])
    assert embedded == data
    assert repo.rsplit("/", 1)[-1] not in json.dumps(embedded)
    assert "/home/" not in page and ".worktrees" not in page
    brigade = embedded["brigades"][0]
    assert brigade["repos"] == ["private-A"]
    assert "url" not in brigade["batches"][0]["epic"]
    assert [frame for frame in brigade["frames"] if frame[1] == "hc"][-1][2] == "active"
    assert brigade["batches"][0]["label"] == "Epic 3"
    assert brigade["cooks"]["cook-1.1"]["label"] == "Cook 1.1"
    assert len(brigade["cooks"]["cook-1.1"]["stories"]) == 2


@pytest.mark.parametrize(
    "outcome", ["failed", "cancelled", "interrupted", "errored", "launch_error"]
)
def test_failed_barrage_stops_until_a_later_attempt_completes(
    replay: ModuleType, outcome: str
) -> None:
    events = [
        fact(0, "pascal", "hc", "pascal_msg", detail={"intent": "reply"}),
        fact(1, "chef", "chef-1", "launch", parent="hc", detail={"label": "Chef 1"}),
        fact(
            2,
            "cook",
            "cook-1.1",
            "launch",
            parent="chef-1",
            detail={"label": "Cook 1.1"},
        ),
    ]
    for second, kind, round_, state in [
        (3, "delegate_start", 1, None),
        (
            4,
            "delegate_error" if outcome == "launch_error" else "delegate_end",
            1,
            outcome,
        ),
        (5, "delegate_start", 2, None),
        (6, "delegate_end", 2, "completed"),
    ]:
        if second == 3 and outcome == "launch_error":
            continue
        events.append(
            fact(
                second,
                "barrage",
                f"barrage:cook-1.1:manic-1:r{round_}",
                kind,
                parent="cook-1.1",
                detail={"sop": "manic-1", "round": round_, "state": state},
            )
        )
    data = replay.board.build(events, set(), {}, {})
    frames = [f for f in data["brigades"][0]["frames"] if f[1] == "cook-1.1/manic-1"]
    assert [
        f[2] for f in frames if f[0] == replay.board.R.ts("2026-01-01T00:00:04Z")
    ] == ["stopped"]
    assert frames[-1][2] == "done"


@pytest.mark.parametrize(
    "value",
    [
        "example-owner/confidential-widget",
        "CONFIDENTIAL-WIDGET",
        "/home/example/topic",
        "/Users/example/topic",
        r"C:\Users\example\topic",
        "~/topic",
        ".worktrees/topic",
    ],
)
def test_private_data_is_refused_before_embedding(
    replay: ModuleType, value: str
) -> None:
    with pytest.raises(replay.ScriptError, match="Privacy check refused the data"):
        replay.render_page(
            {"nested": [{"value": value}]},
            {"example-owner/confidential-widget": "private-A"},
        )


def test_short_private_name_matches_whole_words_only(replay: ModuleType) -> None:
    page = replay.render_page({"state": "todo"}, {"example-owner/do": "private-A"})
    assert '"todo"' in page
    with pytest.raises(replay.ScriptError, match="Privacy check refused the data"):
        replay.render_page({"repo": "do#12"}, {"example-owner/do": "private-A"})


@pytest.mark.parametrize(
    "arguments, code",
    [
        (["--unknown", "--help"], 0),
        (["--unknown"], 2),
        (["--since", "yesterday"], 2),
        (["--db", "-"], 2),
    ],
)
def test_cli_help_and_usage(arguments: list[str], code: int) -> None:
    done = subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == code
    if code == 0:
        assert "examples:" in done.stdout and "exit codes:" in done.stdout
        assert done.stderr == ""
    else:
        assert done.stdout == ""
        answer = json.loads(done.stderr.splitlines()[-1])
        assert answer["ok"] is False
        assert answer["help"] == "replay.py --help"
