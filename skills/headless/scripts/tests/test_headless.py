import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "headless.py"

STUB = """\
import json, os, sys
from pathlib import Path

name, args = Path(sys.argv[0]).name, sys.argv[1:]
if args[:2] in (["login", "status"], ["auth", "status"]):
    sys.exit(1 if os.environ.get("STUB_AUTH_FAIL") else 0)
prompt = sys.stdin.read()
with open(os.environ["STUB_LOG"], "a") as log:
    log.write(json.dumps({"argv": args, "stdin": prompt}) + "\\n")
if os.environ.get("STUB_TOUCH"):
    with open(os.environ["STUB_TOUCH"], "a") as edited:
        edited.write("changed by the child\\n")
answer = os.environ.get("STUB_ANSWER", "No findings.")
if name == "codex":
    model = args[args.index("-m") + 1]
    print(f"model: {model}\\nsession id: stub-codex-session", file=sys.stderr)
    Path(args[args.index("-o") + 1]).write_text(answer)
else:
    session = args[args.index("--resume" if "--resume" in args else "--session-id") + 1]
    denied = [{"tool_name": "Edit"}] if os.environ.get("STUB_DENY") else []
    print(json.dumps({
        "type": "result",
        "is_error": False,
        "result": answer,
        "session_id": session,
        "permission_denials": denied,
        "modelUsage": {args[args.index("--model") + 1]: {}},
    }))
sys.exit(int(os.environ.get("STUB_EXIT", "0")))
"""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    checkout = tmp_path / "repo"
    checkout.mkdir()
    (checkout / "README.md").write_text("demo\n")
    for command in (
        ["git", "init", "-q"],
        ["git", "add", "-A"],
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"],
    ):
        subprocess.run(command, cwd=checkout, check=True)
    return checkout


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    stubs = tmp_path / "bin"
    stubs.mkdir()
    for name in ("codex", "claude"):
        stub = stubs / name
        stub.write_text(f"#!{sys.executable}\n{STUB}")
        stub.chmod(0o755)
    return {
        **os.environ,
        "PATH": f"{stubs}{os.pathsep}{os.environ['PATH']}",
        "STUB_LOG": str(tmp_path / "calls.jsonl"),
        "TMPDIR": str(tmp_path),
    }


def launch(
    env: dict[str, str],
    cwd: Path,
    *args: str,
    prompt: str = "Review README.md.",
    **stub: str,
):
    prompt_file = cwd.parent / "prompt.md"
    prompt_file.write_text(prompt)
    split = args.index("--") if "--" in args else len(args)
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            *args[:split],
            "--prompt-file",
            str(prompt_file),
            "--cwd",
            str(cwd),
            *args[split:],
        ],
        env={**env, **stub},
        capture_output=True,
        text=True,
        check=False,
    )


def calls(env: dict[str, str]) -> list[dict]:
    log = Path(env["STUB_LOG"])
    return (
        [json.loads(line) for line in log.read_text().splitlines()]
        if log.exists()
        else []
    )


def test_codex_review_runs_unsandboxed_and_prints_the_model_that_ran(env, repo):
    done = launch(env, repo, "codex", "--review-only")

    assert done.returncode == 0, done.stderr
    assert done.stdout.splitlines()[:4] == [
        "model: gpt-6.1-sol",
        "effort: xhigh",
        "session: stub-codex-session",
        "changed: nothing",
    ]
    assert done.stdout.endswith("\n\nNo findings.\n")
    [call] = calls(env)
    assert call["argv"][:4] == [
        "exec",
        "-C",
        str(repo),
        "--dangerously-bypass-approvals-and-sandbox",
    ]
    assert call["argv"][4:8] == [
        "-m",
        "gpt-6.1-sol",
        "-c",
        'model_reasoning_effort="xhigh"',
    ]
    assert call["argv"][-1] == "-"
    assert "--ephemeral" not in call["argv"] and "--json" not in call["argv"]
    assert call["stdin"].startswith("Mode: review only. Report your findings only.")
    assert call["stdin"].endswith("\n\nReview README.md.")


def test_claude_fix_may_edit_and_lists_the_changed_file(env, repo):
    done = launch(
        env, repo, "claude", "--review-fix", STUB_TOUCH=str(repo / "README.md")
    )

    assert done.returncode == 0, done.stderr
    assert "changed: README.md" in done.stdout.splitlines()
    assert "model: claude-opus-5-5" in done.stdout.splitlines()
    [call] = calls(env)
    assert call["argv"][:2] == ["-p", "--model"]
    assert "--dangerously-skip-permissions" in call["argv"]
    assert call["argv"][call["argv"].index("--output-format") + 1] == "json"
    assert "--session-id" in call["argv"]
    assert call["stdin"].startswith("Mode: review and fix. You may edit files in")


def test_a_review_that_edits_the_checkout_fails(env, repo):
    done = launch(
        env, repo, "codex", "--review-only", STUB_TOUCH=str(repo / "README.md")
    )

    assert done.returncode == 1
    assert done.stdout == ""
    assert "error: the review-only run changed the checkout: README.md" in done.stderr


@pytest.mark.parametrize(
    ("target", "stub", "message"),
    [
        ("codex", {"STUB_ANSWER": ""}, "error: codex gave no answer"),
        (
            "codex",
            {"STUB_ANSWER": "Review was interrupted. Please re-run /review"},
            "interrupted",
        ),
        ("claude", {"STUB_DENY": "1"}, "error: Claude was denied Edit"),
        ("claude", {"STUB_EXIT": "1"}, "error: claude exited 1"),
    ],
)
def test_an_unusable_answer_fails(env, repo, target, stub, message):
    done = launch(env, repo, target, "--review-only", **stub)

    assert done.returncode == 1
    assert done.stdout == ""
    assert message in done.stderr
    assert "run: " in done.stderr


def test_an_unknown_effort_is_refused_before_launch(env, repo):
    done = launch(env, repo, "claude", "--review-only", "--effort", "minimal")

    assert done.returncode == 2
    assert (
        "--effort minimal is not one of low, medium, high, xhigh, max for claude"
        in done.stderr
    )
    assert calls(env) == []


def test_a_missing_login_names_the_command_that_fixes_it(env, repo):
    done = launch(env, repo, "codex", "--review-only", STUB_AUTH_FAIL="1")

    assert done.returncode == 1
    assert "error: codex is not logged in; run 'codex login', then rerun" in done.stderr
    assert calls(env) == []


def test_flags_after_double_dash_reach_the_child(env, repo):
    done = launch(env, repo, "codex", "--review-only", "--", "-c", 'web_search="live"')

    assert done.returncode == 0, done.stderr
    [call] = calls(env)
    assert call["argv"][8:10] == ["-c", 'web_search="live"']


def test_resume_continues_the_named_session(env, repo):
    codex = launch(env, repo, "codex", "--review-fix", "--resume", "abc")
    claude = launch(env, repo, "claude", "--review-fix", "--resume", "def")

    assert codex.returncode == 0 and claude.returncode == 0
    codex_call, claude_call = calls(env)
    assert codex_call["argv"][:3] == ["exec", "resume", "abc"]
    assert claude_call["argv"][claude_call["argv"].index("--resume") + 1] == "def"
    assert "--session-id" not in claude_call["argv"]


def test_json_prints_the_run_as_one_object(env, repo):
    done = launch(env, repo, "claude", "--review-only", "--json")

    assert done.returncode == 0, done.stderr
    run = json.loads(done.stdout)
    assert run["model"] == "claude-opus-5-5"
    assert run["answer"] == "No findings."
    assert run["changed"] == []
    assert (Path(run["run_dir"]) / "run.json").is_file()
    assert (Path(run["run_dir"]) / "answer.md").read_text() == "No findings."


def test_a_folder_outside_git_warns_and_skips_the_repository_check(env, tmp_path):
    folder = tmp_path / "notes"
    folder.mkdir()
    done = launch(env, folder, "codex", "--review-only")

    assert done.returncode == 0, done.stderr
    assert "is not a Git checkout, so file changes go unchecked" in done.stderr
    [call] = calls(env)
    assert "--skip-git-repo-check" in call["argv"]


def test_claude_review_only_runs_without_its_file_editing_tools(env, repo):
    review = launch(env, repo, "claude", "--review-only")
    fix = launch(env, repo, "claude", "--review-fix")

    assert review.returncode == 0 and fix.returncode == 0
    review_call, fix_call = calls(env)
    denied = review_call["argv"].index("--disallowedTools")
    assert review_call["argv"][denied + 1] == "Edit,Write,NotebookEdit"
    assert "--disallowedTools" not in fix_call["argv"]


@pytest.mark.parametrize("access", [(), ("--review-only", "--review-fix")])
def test_exactly_one_access_flag_is_required(env, repo, access):
    done = launch(env, repo, "codex", *access)

    assert done.returncode == 2
    assert calls(env) == []
