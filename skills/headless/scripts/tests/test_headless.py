import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
import tomllib

SCRIPT = Path(__file__).resolve().parents[1] / "headless.py"
PACKAGE = SCRIPT.parents[1]
SHIPPED = PACKAGE / "config.toml"

CONFIG = """\
harness = "codex"

[codex]
model = "gpt-6.1-sol"
reasoning-level = "xhigh"

[claude]
model = "claude-opus-5-5"
reasoning-level = "xhigh"

[pi]
provider = "openai-codex"
model = "gpt-6.1-sol"
reasoning-level = "high"
"""

STUB = """\
import json, os, subprocess, sys, time
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
if os.environ.get("STUB_RESTAGE"):
    target = Path(os.environ["STUB_RESTAGE"])
    working = target.read_bytes()
    target.write_text("restaged by the child\\n")
    subprocess.run(["git", "add", target.name], cwd=target.parent, check=True)
    target.write_bytes(working)
if os.environ.get("STUB_CORRUPT_INDEX"):
    Path(".git/index").write_bytes(b"not an index")
if os.environ.get("STUB_LINGER"):
    subprocess.Popen([sys.executable, "-c", (
        "import os, signal, sys, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
        "open(sys.argv[1], 'w').write(str(os.getpid())); time.sleep(60)"
    ), os.environ["STUB_LINGER"]])
    # Exit only once the descendant runs, so the launcher has a process to stop
    linger = Path(os.environ["STUB_LINGER"])
    while not (linger.exists() and linger.read_text()):
        time.sleep(0.01)
    if not os.environ.get("STUB_LINGER_EXIT"):
        time.sleep(60)
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
    (tmp_path / "config.toml").write_text(CONFIG)
    return {
        **os.environ,
        "PATH": f"{stubs}{os.pathsep}{os.environ['PATH']}",
        "STUB_LOG": str(tmp_path / "calls.jsonl"),
        "TMPDIR": str(tmp_path),
    }


def command(
    cwd: Path, args: tuple[str, ...], prompt: str | None, shipped: bool = False
) -> list[str]:
    own: list[str] = ["--cwd", str(cwd)]
    if prompt is not None:
        prompt_file = cwd.parent / "prompt.md"
        prompt_file.write_text(prompt)
        own += ["--prompt-file", str(prompt_file)]
    if not shipped:
        own += ["--config", str(cwd.parent / "config.toml")]
    split = args.index("--") if "--" in args else len(args)
    return [sys.executable, str(SCRIPT), *args[:split], *own, *args[split:]]


def launch(
    env: dict[str, str],
    cwd: Path,
    *args: str,
    prompt: str | None = "Review README.md.",
    **stub: str,
):
    return subprocess.run(
        command(cwd, args, prompt),
        env={**env, **stub},
        capture_output=True,
        text=True,
        check=False,
    )


def start(env: dict[str, str], cwd: Path, *args: str, **stub: str):
    return subprocess.Popen(
        command(cwd, args, "Review README.md."),
        env={**env, **stub},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def alive(pid: int) -> bool:
    state = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return bool(state) and not state.startswith("Z")


def wait_for(path: Path) -> int:
    deadline = time.monotonic() + 15
    while not (path.exists() and path.read_text()):
        assert time.monotonic() < deadline, f"{path} never appeared"
        time.sleep(0.05)
    return int(path.read_text())


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


@pytest.mark.parametrize("when", ["before the run", "after the run"])
def test_a_checkout_git_cannot_read_fails_the_run(env, repo, when):
    stub = {"STUB_TOUCH": str(repo / "README.md")}
    if when == "before the run":
        (repo / ".git" / "index").write_bytes(b"not an index")
    else:
        stub["STUB_CORRUPT_INDEX"] = "1"
    done = launch(env, repo, "codex", "--review-only", **stub)

    assert done.returncode == 1
    assert done.stdout == ""
    assert f"cannot read the Git state of {repo.resolve()} {when}" in done.stderr
    if when == "before the run":
        assert calls(env) == []


def test_review_only_fails_when_only_the_staged_content_changed(env, repo):
    readme = repo / "README.md"
    readme.write_text("staged\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    readme.write_text("working\n")
    done = launch(env, repo, "codex", "--review-only", STUB_RESTAGE=str(readme))

    assert readme.read_text() == "working\n"
    assert done.returncode == 1
    assert done.stdout == ""
    assert "error: the review-only run changed the checkout: README.md" in done.stderr


def test_a_timeout_kills_descendants_that_ignore_sigterm(env, repo, tmp_path):
    pid_file = tmp_path / "linger.pid"
    done = launch(
        env, repo, "codex", "--review-fix", "--timeout", "1s", STUB_LINGER=str(pid_file)
    )

    assert done.returncode == 1
    assert "codex ran past --timeout" in done.stderr
    assert not alive(wait_for(pid_file))


@pytest.mark.parametrize(
    ("number", "code"), [(signal.SIGINT, 130), (signal.SIGTERM, 143)]
)
def test_an_interrupt_kills_descendants_that_ignore_sigterm(
    env, repo, tmp_path, number, code
):
    pid_file = tmp_path / "linger.pid"
    process = start(env, repo, "codex", "--review-fix", STUB_LINGER=str(pid_file))
    descendant = wait_for(pid_file)
    process.send_signal(number)
    process.communicate(timeout=60)

    assert process.returncode == code
    assert not alive(descendant)


def test_descendants_left_after_the_child_exits_are_stopped(env, repo, tmp_path):
    pid_file = tmp_path / "linger.pid"
    done = launch(
        env,
        repo,
        "codex",
        "--review-only",
        STUB_LINGER=str(pid_file),
        STUB_LINGER_EXIT="1",
    )

    assert done.returncode == 0, done.stderr
    assert not alive(wait_for(pid_file))


def test_the_shipped_config_sets_the_harness_model_and_reasoning_level(env, repo):
    shipped = tomllib.loads(SHIPPED.read_text())
    harness = shipped["harness"]
    done = subprocess.run(
        command(repo, ("--review-only",), "Review README.md.", shipped=True),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert done.returncode == 0, done.stderr
    [call] = calls(env)
    argv = " ".join(call["argv"])
    assert shipped[harness]["model"] in argv
    assert shipped[harness]["reasoning-level"] in argv
    assert f"effort: {shipped[harness]['reasoning-level']}" in done.stdout.splitlines()


def test_without_a_cli_name_the_config_harness_runs(env, repo, tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(
        config.read_text().replace('harness = "codex"', 'harness = "claude"')
    )
    done = launch(env, repo, "--review-only")

    assert done.returncode == 0, done.stderr
    [call] = calls(env)
    assert call["argv"][:3] == ["-p", "--model", "claude-opus-5-5"]


def test_model_and_effort_flags_win_over_the_config(env, repo):
    done = launch(
        env, repo, "codex", "--review-only", "--model", "gpt-6-astra", "--effort", "low"
    )

    assert done.returncode == 0, done.stderr
    [call] = calls(env)
    assert call["argv"][4:8] == [
        "-m",
        "gpt-6-astra",
        "-c",
        'model_reasoning_effort="low"',
    ]


def test_a_harness_the_launcher_cannot_run_points_to_its_reference(env, repo, tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(config.read_text().replace('harness = "codex"', 'harness = "pi"'))
    done = launch(env, repo, "--review-only")

    assert done.returncode == 2
    assert (
        'sets harness = "pi", which the launcher does not run yet (#281)' in done.stderr
    )
    assert "references/pi/MetaSkill.md" in done.stderr
    assert calls(env) == []


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        (
            ('reasoning-level = "xhigh"', 'reasoning-level = "hihg"'),
            "[codex] reasoning-level 'hihg' is not one of low, medium, high, xhigh, max, ultra",
        ),
        (
            ("[codex]\n", '[codex]\nprovider = "openai"\n'),
            "[codex] takes no provider; codex picks its own",
        ),
        (
            ('provider = "openai-codex"\n', ""),
            "[pi] needs provider, since several providers serve one model",
        ),
        (('harness = "codex"', 'harness = "gemini"'), "harness must be one of codex"),
        (("[claude]", "[gemini]"), "unknown key 'gemini'"),
        (
            ('model = "gpt-6.1-sol"\n', 'model = "gpt-6.1-sol"\nthinking = "x"\n'),
            "unknown key 'thinking'",
        ),
        (("[codex]", "codex = ["), "is not valid TOML"),
        (
            ('harness = "codex"', 'harness = "codex"\nopencode = "x"'),
            "opencode must be a [opencode] table",
        ),
    ],
)
def test_an_invalid_config_names_the_file_and_the_key(
    env, repo, tmp_path, edit, message
):
    config = tmp_path / "config.toml"
    config.write_text(config.read_text().replace(*edit, 1))
    done = launch(env, repo, "codex", "--review-only")

    assert done.returncode == 1
    assert done.stdout == ""
    assert f"error: {config}" in done.stderr
    assert message in done.stderr
    assert calls(env) == []


def test_a_missing_config_says_how_to_point_at_another(env, repo, tmp_path):
    (tmp_path / "config.toml").unlink()
    done = launch(env, repo, "codex", "--review-only")

    assert done.returncode == 1
    assert "cannot read the config" in done.stderr
    assert "pass --config FILE" in done.stderr


def test_the_docs_repeat_no_model_from_the_config():
    shipped = tomllib.loads(SHIPPED.read_text())
    models = {table["model"] for table in shipped.values() if isinstance(table, dict)}
    repeats = [
        f"{doc.relative_to(PACKAGE)} names {model}"
        for doc in PACKAGE.rglob("*.md")
        for model in models
        if model in doc.read_text()
    ]

    assert repeats == []


def test_code_review_runs_codex_review_read_only_on_the_review_model(env, repo):
    subprocess.run(["git", "branch", "main"], cwd=repo, check=False)
    done = launch(env, repo, "--code-review", "--base", "main", prompt=None)

    assert done.returncode == 0, done.stderr
    assert done.stdout.splitlines()[:2] == ["model: gpt-6.1-sol", "effort: xhigh"]
    [call] = calls(env)
    assert call["argv"][:2] == ["exec", "review"]
    assert call["argv"][2:6] == [
        "-c",
        'sandbox_mode="read-only"',
        "-c",
        'approval_policy="never"',
    ]
    assert 'review_model="gpt-6.1-sol"' in call["argv"]
    assert "--dangerously-bypass-approvals-and-sandbox" not in call["argv"]
    assert call["argv"][-2:] == ["--base", "main"]


def test_code_review_passes_its_diff_target(env, repo):
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    uncommitted = launch(env, repo, "--code-review", "--uncommitted", prompt=None)
    commit = launch(
        env, repo, "--code-review", "--commit", sha, "--title", "Fix it", prompt=None
    )

    assert uncommitted.returncode == 0 and commit.returncode == 0, commit.stderr
    uncommitted_call, commit_call = calls(env)
    assert uncommitted_call["argv"][-1:] == ["--uncommitted"]
    assert commit_call["argv"][-4:] == ["--commit", sha, "--title", "Fix it"]


@pytest.mark.parametrize("flag", ["--base", "--commit"])
def test_a_diff_target_git_cannot_find_stops_before_launch(env, repo, flag):
    done = launch(env, repo, "--code-review", flag, "origin/gone", prompt=None)

    assert done.returncode == 2
    assert f"{flag} origin/gone names no commit" in done.stderr
    assert "run 'git fetch'" in done.stderr
    assert calls(env) == []


def test_code_review_with_a_prompt_file_sends_custom_instructions(env, repo):
    done = launch(env, repo, "--code-review", prompt="Focus on error handling.")

    assert done.returncode == 0, done.stderr
    [call] = calls(env)
    assert call["argv"][-1] == "-"
    assert call["stdin"] == "Focus on error handling."


def test_code_review_runs_codex_even_when_the_config_harness_is_claude(
    env, repo, tmp_path
):
    config = tmp_path / "config.toml"
    config.write_text(
        config.read_text().replace('harness = "codex"', 'harness = "claude"')
    )
    done = launch(env, repo, "--code-review", "--uncommitted", prompt=None)

    assert done.returncode == 0, done.stderr
    [call] = calls(env)
    assert call["argv"][:2] == ["exec", "review"]


def test_a_code_review_that_edits_the_checkout_fails(env, repo):
    done = launch(
        env,
        repo,
        "--code-review",
        "--uncommitted",
        prompt=None,
        STUB_TOUCH=str(repo / "README.md"),
    )

    assert done.returncode == 1
    assert "error: the code-review run changed the checkout: README.md" in done.stderr


@pytest.mark.parametrize(
    ("args", "prompt", "message"),
    [
        (
            ("--code-review",),
            None,
            "needs exactly one of --base, --uncommitted, --commit",
        ),
        (("--code-review", "--base", "main"), "x", "needs exactly one of"),
        (("--code-review", "--uncommitted", "--resume", "abc"), None, "cannot resume"),
        (("claude", "--code-review", "--uncommitted"), None, "runs Codex only"),
        (
            ("codex", "--review-only", "--base", "main"),
            "x",
            "--base works only with --code-review",
        ),
        (
            ("codex", "--review-only", "--title", "t"),
            "x",
            "--title works only with --code-review",
        ),
        (("codex", "--review-fix"), None, "--review-fix needs --prompt-file"),
    ],
)
def test_code_review_usage_errors_stop_before_launch(env, repo, args, prompt, message):
    done = launch(env, repo, *args, prompt=prompt)

    assert done.returncode == 2
    assert message in done.stderr
    assert calls(env) == []


def test_code_review_outside_git_is_a_usage_error(env, tmp_path):
    folder = tmp_path / "notes"
    folder.mkdir()
    done = launch(env, folder, "--code-review", "--uncommitted", prompt=None)

    assert done.returncode == 2
    assert "is not a Git checkout" in done.stderr
    assert calls(env) == []
