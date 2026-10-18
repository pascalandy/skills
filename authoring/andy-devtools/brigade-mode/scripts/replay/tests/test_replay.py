"""Synthetic replay output and the command's public CLI boundary."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "replay.py"


def test_private_run_keeps_epic_cook_and_story_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("brigade_replay_command", SCRIPT)
    assert spec and spec.loader
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    repo = "example-owner/confidential-widget"

    def fact(second: int, role: str, thread: str, kind: str, **fields: object) -> dict:
        event = dict.fromkeys(replay.facts.KEYS)
        event.update(
            time=f"2026-01-01T00:00:{second:02d}.000Z",
            brigade="abcd",
            role=role,
            thread=thread,
            kind=kind,
        )
        event.update(fields)
        return event

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
        fact(
            8,
            "head_chef",
            "hc",
            "rename",
            status="⏳",
            detail={
                "counter": "0/1",
                "title": f"Head Chef abcd 0/1 ⏳ {repo} /home/example/.worktrees/private-topic",
            },
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
    assert "confidential-widget" not in page
    assert "/home/" not in page and ".worktrees" not in page
    brigade = data["brigades"][0]
    assert brigade["repos"] == ["private-A"]
    assert "url" not in brigade["batches"][0]["epic"]
    assert brigade["titles"][0][1] == "Head Chef abcd 0/1 ⏳"
    assert [frame for frame in brigade["frames"] if frame[1] == "hc"][-1][2] == "active"

    script = re.search(r"<script>(.*?)</script>", page, re.DOTALL)
    assert script
    words = subprocess.run(
        [
            "node",
            "-e",
            script[1].split("const BOARD =", 1)[0]
            + """
const br = DATA.brigades[0];
console.log(JSON.stringify({
  epic: ui.say.epic(br, {}, br.batches[0], br.start).name,
  cook: ui.say.cook(br, {}, "cook-1.1", br.start).name,
  stories: ui.say.cook(br, {}, "cook-1.1", br.start).stories,
}));
""",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(words.stdout) == {
        "epic": "Epic 3",
        "cook": "Cook 1.1",
        "stories": "2 Stories",
    }


@pytest.mark.parametrize(
    "arguments, code",
    [(["--unknown", "--help"], 0), (["--unknown"], 2), (["--since", "yesterday"], 2)],
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
