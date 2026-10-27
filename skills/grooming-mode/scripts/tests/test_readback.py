"""Exercise the installed CLI boundary with fake gh, never public issue writes."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).parents[1] / "readback.py"
REF = "pascalandy/skills#335"
PARENT = "pascalandy/skills#969"

FAKE_GH = r"""
import json, os, re, sys, time
from pathlib import Path
assert sys.argv[1:] == ["api", "--hostname", "github.com", "graphql", "--input", "-"]
request = json.load(sys.stdin)
assert request["query"].startswith("query(") and "mutation" not in request["query"]
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as stream:
    stream.write(json.dumps(request) + "\n")
variables = request["variables"]
key = f"{variables['owner']}/{variables['repo']}#{variables['number']}"
page = re.search(r'(labels|subIssues|blockedBy)\(first:100,after:"([^"]+)"\)', request["query"])
if page:
    key += ":" + page[1] + ":" + page[2]
response = json.loads(Path(os.environ["FAKE_RESPONSES"]).read_text(encoding="utf-8"))[key]
if "delay" in response:
    time.sleep(response["delay"])
if "exit" in response:
    sys.stderr.write(response["stderr"])
    sys.exit(response["exit"])
sys.stdout.write(response["raw"] if "raw" in response else json.dumps(response))
"""


def url(ref: str) -> str:
    repo, number = ref.split("#")
    return f"https://github.com/{repo}/issues/{number}"


def connection(values: list[str], *, labels: bool = False) -> dict[str, Any]:
    return {
        "totalCount": len(values),
        "nodes": [
            {"name": value} if labels else {"url": url(value)} for value in values
        ],
        "pageInfo": {"hasNextPage": False, "endCursor": None},
    }


def issue() -> dict[str, Any]:
    return {
        "url": url(REF),
        "body": "Story body",
        "state": "OPEN",
        "parent": {"url": url(PARENT)},
        "subIssues": connection([]),
        "labels": connection(["2-type:feature", "1-ready-for-agent"], labels=True),
        "blockedBy": connection(["other/project#7", "pascalandy/skills#10"]),
    }


def plan() -> dict[str, Any]:
    return {
        "issues": [
            {
                "repo": "pascalandy/skills",
                "number": 335,
                "parent": PARENT,
                "stories": [],
                "labels": ["1-ready-for-agent", "2-type:feature"],
                "blocked_by": ["pascalandy/skills#10", "other/project#7"],
                "state": "OPEN",
            }
        ]
    }


def response(item: dict[str, Any]) -> dict[str, Any]:
    return {"data": {"repository": {"issue": item}}}


def run(
    tmp_path: Path,
    approved: dict[str, Any],
    responses: dict[str, Any],
    *args: str,
    stdin: bool = False,
) -> subprocess.CompletedProcess[str]:
    fake = tmp_path / "gh"
    fake.write_text(f"#!{sys.executable}\n{FAKE_GH}", encoding="utf-8")
    fake.chmod(0o700)
    data = tmp_path / "responses.json"
    data.write_text(json.dumps(responses), encoding="utf-8")
    source = tmp_path / "plan.json"
    source.write_text(json.dumps(approved), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "-" if stdin else str(source), *args],
        input=json.dumps(approved) if stdin else None,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
        env={
            **os.environ,
            "PATH": str(tmp_path),
            "FAKE_RESPONSES": str(data),
            "FAKE_LOG": str(tmp_path / "requests.jsonl"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPYCACHEPREFIX": str(tmp_path / "pycache"),
        },
    )


def failure(result: subprocess.CompletedProcess[str], code: int = 1) -> dict[str, Any]:
    assert result.returncode == code, result.stderr
    assert result.stdout == ""
    answer = json.loads(result.stderr.splitlines()[-1])
    assert answer["ok"] is False
    return answer


def test_full_match_compares_sets_and_reads_stdin(tmp_path: Path) -> None:
    result = run(tmp_path, plan(), {REF: response(issue())}, stdin=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout == '{"ok":true}\n'
    assert result.stderr == ""


@pytest.mark.parametrize(
    ("field", "changed", "expected", "actual"),
    [
        ("parent", None, PARENT, None),
        ("subIssues", connection(["other/project#335"]), [], ["other/project#335"]),
        (
            "labels",
            connection(["2-type:bug"], labels=True),
            ["1-ready-for-agent", "2-type:feature"],
            ["2-type:bug"],
        ),
        (
            "blockedBy",
            connection(["other/project#8"]),
            ["other/project#7", "pascalandy/skills#10"],
            ["other/project#8"],
        ),
        ("state", "CLOSED", "OPEN", "CLOSED"),
    ],
)
def test_each_field_difference(
    tmp_path: Path, field: str, changed: Any, expected: Any, actual: Any
) -> None:
    item = issue()
    item[field] = changed
    answer = failure(run(tmp_path, plan(), {REF: response(item)}))
    assert answer["differences"] == [
        {
            "issue": REF,
            "field": {"subIssues": "stories", "blockedBy": "blocked_by"}.get(
                field, field
            ),
            "expected": expected,
            "actual": actual,
        }
    ]


def test_reports_all_differences_across_issues(tmp_path: Path) -> None:
    approved = plan()
    other = copy.deepcopy(approved["issues"][0])
    other.update(repo="other/project", number=335)
    approved["issues"].append(other)
    first, second = issue(), issue()
    first.update(parent=None, state="CLOSED")
    second.update(url=url("other/project#335"), parent=None)
    answer = failure(
        run(
            tmp_path,
            approved,
            {REF: response(first), "other/project#335": response(second)},
        )
    )
    assert [(d["issue"], d["field"]) for d in answer["differences"]] == [
        (REF, "parent"),
        (REF, "state"),
        ("other/project#335", "parent"),
    ]


@pytest.mark.parametrize("field", ["subIssues", "labels", "blockedBy"])
def test_pages_each_connection_past_100(tmp_path: Path, field: str) -> None:
    approved, item = plan(), issue()
    values = [
        f"label-{i}" if field == "labels" else f"other/project#{i}"
        for i in range(1, 102)
    ]
    approved["issues"][0][
        {"subIssues": "stories", "labels": "labels", "blockedBy": "blocked_by"}[field]
    ] = values
    page1, page2 = (
        connection(values[:100], labels=field == "labels"),
        connection(values[100:], labels=field == "labels"),
    )
    page1.update(totalCount=101, pageInfo={"hasNextPage": True, "endCursor": "next"})
    page2["totalCount"] = 101
    item[field] = page1
    result = run(
        tmp_path,
        approved,
        {
            REF: response(item),
            REF + ":" + field + ":next": response({"url": url(REF), field: page2}),
        },
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == '{"ok":true}\n'
    assert (
        len((tmp_path / "requests.jsonl").read_text(encoding="utf-8").splitlines()) == 2
    )


def test_native_order_is_not_a_set(tmp_path: Path) -> None:
    approved, item = plan(), issue()
    approved["issues"][0]["stories"] = ["other/project#1", "other/project#2"]
    item["subIssues"] = connection(["other/project#2", "other/project#1"])
    answer = failure(run(tmp_path, approved, {REF: response(item)}))
    assert answer["differences"][0] == {
        "issue": REF,
        "field": "stories",
        "expected": ["other/project#1", "other/project#2"],
        "actual": ["other/project#2", "other/project#1"],
    }


@pytest.mark.parametrize(
    "body,actual",
    [
        (
            "## Stories\n\n1. **One** (#1) · code + tests\n   - **Today:** #9\n2. **Two** (other/project#2) · text\n\n## Done when\nDone",
            ["pascalandy/skills#1", "other/project#2"],
        ),
        (
            "## Stories\n\n1. **Two** (other/project#2) · text\n2. **One** (#1) · text\n",
            ["other/project#2", "pascalandy/skills#1"],
        ),
        ("No Stories section", None),
        ("## Stories\n1. Missing reference\n", None),
        ("## Stories\n## Stories\n", None),
        (
            "## Stories\n1. **Unexpected Story** (#999) · code + tests (#1) · text\n2. **Two** (other/project#2) · text\n",
            None,
        ),
        (
            "## Stories\n1. **Unexpected Story** (#999) · **Extra title** (#1) · text\n2. **Two** (other/project#2) · text\n",
            None,
        ),
        (
            "```md\n## Stories\n1. **One** (#1) · code + tests\n2. **Two** (other/project#2) · text\n## Done when\nDone\n```\n",
            None,
        ),
        (
            "~~~md\n## Stories\n1. **One** (#1) · code + tests\n2. **Two** (other/project#2) · text\n## Done when\nDone\n~~~\n",
            None,
        ),
        (
            "```md\n## Stories\n1. **Example** (#999) · text\n```\n## Stories\n1. **One** (#1) · code + tests\n2. **Two** (other/project#2) · text\n## Done when\nDone\n",
            ["pascalandy/skills#1", "other/project#2"],
        ),
        (
            "```markdown```\n## Stories\n1. **Unexpected Story** (#999) · text\n```\n## Stories\n1. **One** (#1) · code + tests\n2. **Two** (other/project#2) · text\n",
            None,
        ),
        (
            "```md\n```\u00a0\n## Stories\n1. **One** (#1) · code + tests\n2. **Two** (other/project#2) · text\n",
            None,
        ),
        (
            "```markdown```\n## Stories\n1. **One** (#1) · code + tests\n2. **Two** (other/project#2) · text\n",
            ["pascalandy/skills#1", "other/project#2"],
        ),
        (
            "```md\n```\u2028## Stories\n1. **One** (#1) · code + tests\n2. **Two** (other/project#2) · text\n",
            None,
        ),
        (
            "## Stories\n1. **One** (#1) · code + tests\u20282. **Two** (other/project#2) · text\n",
            None,
        ),
    ],
)
def test_epic_body_agrees_with_native_order(
    tmp_path: Path, body: str, actual: Any
) -> None:
    approved, item = plan(), issue()
    stories = ["pascalandy/skills#1", "other/project#2"]
    approved["issues"][0].update(stories=stories, labels=["4-epic"])
    item.update(
        body=body,
        labels=connection(["4-epic"], labels=True),
        subIssues=connection(stories),
    )
    result = run(tmp_path, approved, {REF: response(item)})
    if actual == stories:
        assert result.returncode == 0, result.stderr
        assert result.stdout == '{"ok":true}\n'
    else:
        assert failure(result)["differences"] == [
            {
                "issue": REF,
                "field": "body_stories",
                "expected": stories,
                "actual": actual,
            }
        ]


@pytest.mark.parametrize("field", ["subIssues", "labels", "blockedBy"])
@pytest.mark.parametrize("broken", ["missing", "truncated", "no-cursor", "null-node"])
def test_incomplete_relations_fail(tmp_path: Path, field: str, broken: str) -> None:
    item = issue()
    if broken == "missing":
        del item[field]
    elif broken == "truncated":
        item[field]["totalCount"] += 1
    elif broken == "no-cursor":
        item[field]["pageInfo"] = {"hasNextPage": True, "endCursor": None}
    else:
        item[field]["nodes"] = [None]
    answer = failure(run(tmp_path, plan(), {REF: response(item)}))
    assert REF in answer["errors"][0]
    assert f"incomplete {field}" in answer["errors"][0]


@pytest.mark.parametrize(
    "entry,actual",
    [
        ("  1. **Unexpected Story** (#631) · code + tests", ["pascalandy/skills#631"]),
        ("  1) **Unexpected Story** (#631) · code + tests", None),
        ("   - **Today:** orphan detail", None),
    ],
)
def test_indented_story_entry_is_not_ignored(
    tmp_path: Path, entry: str, actual: Any
) -> None:
    approved, item = plan(), issue()
    approved["issues"][0]["labels"] = ["4-epic"]
    item.update(
        labels=connection(["4-epic"], labels=True),
        body=f"## Stories\n\n{entry}\n",
    )
    answer = failure(run(tmp_path, approved, {REF: response(item)}))
    assert answer["differences"] == [
        {
            "issue": REF,
            "field": "body_stories",
            "expected": [],
            "actual": actual,
        }
    ]


@pytest.mark.parametrize(
    "broken", ["gh-failure", "changed-count", "repeated-cursor", "duplicate-node"]
)
def test_second_page_failures_cannot_pass(tmp_path: Path, broken: str) -> None:
    item = issue()
    item["subIssues"] = connection(["other/project#1"])
    item["subIssues"].update(
        totalCount=2, pageInfo={"hasNextPage": True, "endCursor": "next"}
    )
    second = connection(["other/project#2"])
    second["totalCount"] = 2
    if broken == "changed-count":
        second["totalCount"] = 3
    elif broken == "repeated-cursor":
        second["pageInfo"] = {"hasNextPage": True, "endCursor": "next"}
    elif broken == "duplicate-node":
        second["nodes"] = [{"url": url("other/project#1")}]
    payload = (
        {"exit": 1, "stderr": "permission denied"}
        if broken == "gh-failure"
        else response({"url": url(REF), "subIssues": second})
    )
    answer = failure(
        run(tmp_path, plan(), {REF: response(item), REF + ":subIssues:next": payload})
    )
    assert REF in answer["errors"][0]
    assert "differences" not in answer


@pytest.mark.parametrize(
    "payload",
    [
        {"exit": 1, "stderr": "authentication failed"},
        {"raw": "not JSON"},
        {"data": {"repository": {"issue": None}}},
        {
            "errors": [{"message": "hidden relation"}],
            "data": {"repository": {"issue": issue()}},
        },
    ],
)
def test_failed_or_partial_github_reads_fail(tmp_path: Path, payload: Any) -> None:
    answer = failure(run(tmp_path, plan(), {REF: payload}))
    assert REF in answer["errors"][0]


def test_timeout_is_safe_to_retry(tmp_path: Path) -> None:
    answer = failure(
        run(tmp_path, plan(), {REF: {"delay": 1}}, "--timeout", "0.05s"), 75
    )
    assert REF in answer["errors"][0]
    assert "retry" in answer


@pytest.mark.parametrize(
    "change", ["missing-parent", "bad-ref", "duplicate-issue", "empty"]
)
def test_invalid_plan_fails_before_github(tmp_path: Path, change: str) -> None:
    approved = plan()
    if change == "missing-parent":
        del approved["issues"][0]["parent"]
    elif change == "bad-ref":
        approved["issues"][0]["parent"] = "#969"
    elif change == "duplicate-issue":
        approved["issues"].append(copy.deepcopy(approved["issues"][0]))
    else:
        approved["issues"] = []
    answer = failure(run(tmp_path, approved, {}), 2)
    assert answer["help"].endswith(" --help")
    assert not (tmp_path / "requests.jsonl").exists()
