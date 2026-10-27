"""Exercise the offline preview with frozen historical bodies and real Git merges."""

import hashlib
import json
import os
import shlex
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "merge-principles.sh"
FIXTURES = Path(__file__).parent / "fixtures" / "merge-principles"
GIT = shutil.which("git")
PRINCIPLES = Path("authoring/poteto/poteto-mode/principles")
PROVE = Path("authoring/poteto/principle-prove-it-works/SKILL.md")
CONFLICTS = {
    "attack-the-premise": 1,
    "build-the-lever": 1,
    "fix-root-causes": 2,
    "minimize-reader-load": 1,
    "sequence-verifiable-units": 1,
    "type-system-discipline": 1,
}


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        [GIT, "-C", str(repo), *args], text=True, encoding="utf-8"
    ).strip()


def init(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-b", "main")


def commit(repo: Path) -> str:
    git(repo, "add", ".")
    git(
        repo,
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "--allow-empty",
        "-m",
        "fixture",
    )
    return git(repo, "rev-parse", "HEAD")


def write(repo: Path, path: Path, body: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")


def snapshot(repo: Path) -> tuple:
    files = {
        str(p.relative_to(repo)): p.read_bytes()
        for p in repo.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(repo).parts
    }
    return (
        files,
        git(repo, "rev-parse", "HEAD"),
        git(repo, "for-each-ref"),
        git(repo, "status", "--porcelain"),
    )


@pytest.fixture
def offline(tmp_path: Path) -> dict[str, str]:
    """Deny Git network/mutations and record calls made by the actual CLI."""
    tools = tmp_path / "bin"
    tools.mkdir()
    wrapper = tools / "git"
    wrapper.write_text(
        "#!/usr/bin/env bash\n"
        'printf "%s\\n" "$*" >>"$GIT_CALLS"\n'
        'args=("$@")\n[[ "${1:-}" != --no-lazy-fetch ]] || shift\n'
        '[[ "${1:-}" != -C ]] || shift 2\n'
        'case "${1:-}" in --version|rev-parse|ls-tree|show|merge-file) ;; *) exit 90;; esac\n'
        f'exec {shlex.quote(GIT)} "${{args[@]}}"\n',
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    return {
        **os.environ,
        "PATH": f"{tools}{os.pathsep}{os.environ['PATH']}",
        "GIT_CALLS": str(tmp_path / "git-calls"),
        "TMPDIR": str(tmp_path),
    }


def run(
    root: Path, upstream: Path, base: str, head: str, env: dict[str, str], *args: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), str(root), str(upstream), base, head, *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        env=env,
    )


def answer(result: subprocess.CompletedProcess[str]) -> dict:
    if result.returncode == 0:
        assert len(result.stdout.splitlines()) == 1
        data = json.loads(result.stdout)
        assert result.stderr == ""
    else:
        assert result.stdout == ""
        data = json.loads(result.stderr.splitlines()[-1])
    assert data["ok"] is (result.returncode == 0)
    return data


def strip_frontmatter(data: str) -> str:
    if data.startswith("---\n"):
        return data.split("\n---\n", 1)[1]
    return data


def install_snapshot(kind: str, repo: Path) -> None:
    for source in json.loads((FIXTURES / "sources.json").read_text(encoding="utf-8")):
        if source["snapshot"] == kind:
            target = repo / source["source"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(FIXTURES / source["file"], target)


def test_historical_preview_finishes_all_merges_without_writes(
    tmp_path: Path,
    offline: dict[str, str],
) -> None:
    for source in json.loads((FIXTURES / "sources.json").read_text(encoding="utf-8")):
        assert (
            hashlib.sha256((FIXTURES / source["file"]).read_bytes()).hexdigest()
            == source["sha256"]
        )
    local, upstream = tmp_path / "local tree", tmp_path / "upstream tree"
    init(local)
    install_snapshot("local", local)
    write(
        local,
        Path("authoring/poteto/poteto-mode/references/pstack-sync.md"),
        "Keep this ledger.\n",
    )
    commit(local)
    init(upstream)
    install_snapshot("base", upstream)
    base = commit(upstream)
    install_snapshot("head", upstream)
    head = commit(upstream)
    before = snapshot(local), snapshot(upstream)
    result = run(local, upstream, base, head, offline)
    assert result.returncode == 1
    report = json.loads(Path(answer(result)["file"]).read_text(encoding="utf-8"))
    assert list(report) == ["records", "bodies"]
    records = report["records"]
    assert Counter(r["state"] for r in records) == {
        "conflict": 6,
        "clean": 17,
        "new-upstream": 1,
    }
    conflicts = {
        Path(r["path"]).stem: r["conflict_blocks"]
        for r in records
        if r["state"] == "conflict"
    }
    assert conflicts == CONFLICTS
    assert {r["path"]: r["state"] for r in records}[str(PROVE)] == "clean"
    assert next(r for r in records if r["state"] == "new-upstream")["path"] == str(
        PRINCIPLES / "explain-the-number.md"
    )
    bodies = {r["path"]: r["body"] for r in report["bodies"]}
    assert len(bodies) == len(records) == 24
    for record in records:
        path = record["path"]
        name = "prove-it-works" if path == str(PROVE) else Path(path).stem
        source = Path(f"{name}.md")
        if record["state"] == "new-upstream":
            assert bodies[path] == (FIXTURES / "head" / source).read_text(
                encoding="utf-8"
            )
            continue
        oracle_local = tmp_path / "oracle-local"
        oracle_local.write_text(
            strip_frontmatter((local / path).read_text(encoding="utf-8")),
            encoding="utf-8",
        )
        oracle = subprocess.run(
            [
                GIT,
                "merge-file",
                "-p",
                "--diff3",
                "-L",
                "local",
                "-L",
                "base",
                "-L",
                "upstream",
                str(oracle_local),
                str(FIXTURES / "base" / source),
                str(FIXTURES / "head" / source),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        assert oracle.returncode == record["conflict_blocks"]
        assert bodies[path] == oracle.stdout
    assert before == (snapshot(local), snapshot(upstream))


@pytest.mark.parametrize("state", ["new-upstream", "local-only"])
def test_additions_are_success_and_local_reads_working_tree(
    tmp_path: Path,
    offline: dict[str, str],
    state: str,
) -> None:
    local, upstream = tmp_path / "local", tmp_path / "upstream"
    init(local)
    (local / PRINCIPLES).mkdir(parents=True)
    path = PRINCIPLES / "sample.md"
    if state == "local-only":
        write(local, path, "Committed old body.\n")
    commit(local)
    if state == "local-only":
        write(local, path, "Working tree body.\n")
    init(upstream)
    write(upstream, Path("pstack/skills/README.md"), "Principle skills.\n")
    base = commit(upstream)
    if state == "new-upstream":
        write(
            upstream,
            Path("pstack/skills/principle-sample/SKILL.md"),
            '---\nname: "sample"\n---\nWorking tree body.\n',
        )
    head = commit(upstream)
    before = snapshot(local), snapshot(upstream)
    report_path = tmp_path / "report with spaces.json"
    result = run(local, upstream, base, head, offline, f"--output={report_path}")
    assert result.returncode == 0
    assert answer(result) == {"ok": True, "file": str(report_path)}
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report == {
        "records": [{"path": str(path), "state": state, "conflict_blocks": 0}],
        "bodies": [{"path": str(path), "body": "Working tree body.\n"}],
    }
    assert before == (snapshot(local), snapshot(upstream))


@pytest.mark.parametrize("missing", ["base", "head"])
def test_invalid_ref_fails_before_any_merge_or_report(
    tmp_path: Path,
    offline: dict[str, str],
    missing: str,
) -> None:
    local, upstream = tmp_path / "local", tmp_path / "upstream"
    init(local)
    write(local, PRINCIPLES / "sample.md", "Local\n")
    commit(local)
    init(upstream)
    write(upstream, Path("pstack/skills/principle-sample/SKILL.md"), "Upstream\n")
    valid = commit(upstream)
    before = snapshot(local), snapshot(upstream)
    report = tmp_path / "must-not-exist.json"
    ref = f"missing-{missing}"
    result = run(
        local,
        upstream,
        ref if missing == "base" else valid,
        ref if missing == "head" else valid,
        offline,
        "--output",
        str(report),
    )
    assert result.returncode == 2
    data = answer(result)
    assert ref in " ".join(data["errors"])
    assert "file" not in data
    assert not report.exists()
    assert "merge-file" not in Path(offline["GIT_CALLS"]).read_text(encoding="utf-8")
    assert before == (snapshot(local), snapshot(upstream))


def test_help_wins_and_usage_errors_are_json(
    tmp_path: Path, offline: dict[str, str]
) -> None:
    result = run(tmp_path, tmp_path, "base", "head", offline, "--typo", "--help")
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert result.stderr == ""
    result = run(tmp_path, tmp_path, "base", "head", offline, "--typo")
    assert result.returncode == 2
    assert answer(result)["help"] == "merge-principles.sh --help"


@pytest.fixture
def comparison(tmp_path: Path) -> tuple[Path, Path, str, str]:
    local, upstream = tmp_path / "local", tmp_path / "upstream"
    init(local)
    write(local, PRINCIPLES / "sample.md", "Sample body.\n")
    commit(local)
    init(upstream)
    write(upstream, Path("README.md"), "Not the pstack layout.\n")
    wrong = commit(upstream)
    write(upstream, Path("pstack/skills/principle-sample/SKILL.md"), "Sample body.\n")
    valid = commit(upstream)
    return local, upstream, wrong, valid


@pytest.mark.parametrize(
    "kind", ["existing", "symlink", "dangling", "device", "stream", "missing-parent"]
)
def test_report_destination_requires_a_new_regular_file(
    tmp_path: Path,
    offline: dict[str, str],
    comparison: tuple,
    kind: str,
) -> None:
    local, upstream, _, valid = comparison
    sentinel = tmp_path / "sentinel.json"
    sentinel.write_text("Preserve me.\n", encoding="utf-8")
    destination = tmp_path / "report.json"
    if kind == "existing":
        destination = sentinel
    elif kind in ("symlink", "dangling"):
        destination.symlink_to(
            sentinel if kind == "symlink" else tmp_path / "not-created"
        )
    elif kind == "device":
        destination = Path("/dev/null")
    elif kind == "stream":
        destination = Path("/dev/stdout")
    else:
        destination = tmp_path / "missing-parent" / "report.json"
    before = snapshot(local), snapshot(upstream)
    result = run(local, upstream, valid, valid, offline, "--output", str(destination))
    assert result.returncode == 2
    data = answer(result)
    assert "file" not in data and str(destination) in " ".join(data["errors"])
    assert sentinel.read_text(encoding="utf-8") == "Preserve me.\n"
    assert not (tmp_path / "not-created").exists()
    assert "merge-file" not in Path(offline["GIT_CALLS"]).read_text(encoding="utf-8")
    assert before == (snapshot(local), snapshot(upstream))


@pytest.mark.parametrize("missing", ["local", "base", "head"])
def test_wrong_input_layout_is_not_a_clean_preview(
    tmp_path: Path,
    offline: dict[str, str],
    comparison: tuple,
    missing: str,
) -> None:
    local, upstream, wrong, valid = comparison
    root = local
    if missing == "local":
        root = tmp_path / "wrong-root"
        root.mkdir()
    report = tmp_path / "must-not-exist.json"
    result = run(
        root,
        upstream,
        wrong if missing == "base" else valid,
        wrong if missing == "head" else valid,
        offline,
        "--output",
        str(report),
    )
    assert result.returncode == 2
    data = answer(result)
    expected = (
        "authoring/poteto/poteto-mode/principles"
        if missing == "local"
        else "pstack/skills"
    )
    assert expected in " ".join(data["errors"])
    assert "file" not in data and not report.exists()
    calls = Path(offline["GIT_CALLS"])
    assert not calls.exists() or "merge-file" not in calls.read_text(encoding="utf-8")


@pytest.mark.parametrize("args", [("--output=",), ("--output", ""), ("-o", "")])
def test_empty_output_forms_are_the_same_usage_error(
    offline: dict[str, str],
    comparison: tuple,
    args: tuple[str, ...],
) -> None:
    local, upstream, _, valid = comparison
    result = run(local, upstream, valid, valid, offline, *args)
    assert result.returncode == 2
    assert answer(result)["errors"] == [
        "Missing output path; run merge-principles.sh --help"
    ]


def test_relative_local_root_ignores_cdpath(
    tmp_path: Path,
    offline: dict[str, str],
    comparison: tuple,
) -> None:
    _, upstream, _, valid = comparison
    result = subprocess.run(
        ["bash", str(SCRIPT), "local", str(upstream), valid, valid],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        cwd=tmp_path,
        env={**offline, "CDPATH": str(tmp_path)},
    )
    assert result.returncode == 0
    report = json.loads(Path(answer(result)["file"]).read_text(encoding="utf-8"))
    assert report["records"] == [
        {"path": str(PRINCIPLES / "sample.md"), "state": "clean", "conflict_blocks": 0}
    ]


def test_git_without_offline_flag_fails_before_reading_refs(
    tmp_path: Path,
    offline: dict[str, str],
) -> None:
    wrapper = tmp_path / "bin" / "git"
    wrapper.write_text(
        '#!/usr/bin/env bash\nprintf "%s\\n" "$*" >>"$GIT_CALLS"\nexit 129\n',
        encoding="utf-8",
    )
    result = run(tmp_path, tmp_path, "base", "head", offline)
    assert result.returncode == 1
    data = answer(result)
    assert "--no-lazy-fetch support" in " ".join(data["errors"])
    assert "file" not in data
    assert (
        Path(offline["GIT_CALLS"]).read_text(encoding="utf-8")
        == "--no-lazy-fetch --version\n"
    )
