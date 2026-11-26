"""Run rust_guard.py against throwaway crates and git repositories.

The crates never compile: each test writes a Cargo.lock so init skips
`cargo generate-lockfile`, and audit runs without --violations, so no test
needs a Rust toolchain.
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import tomllib

SCRIPT = Path(__file__).resolve().parents[1] / "rust_guard.py"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}

CRATE = """\
[package]
name = "demo"
version = "0.1.0"
edition = "2024"

[dependencies]
"""

LIB = """\
pub fn add(a: u8, b: u8) -> Option<u8> {
    a.checked_add(b)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn adds() {
        assert_eq!(add(1, 2), Some(3));
    }
}
"""


def run(cwd: Path, *args: str) -> tuple[int, dict, str]:
    """Run the script; return its exit code, its JSON answer, and stderr."""
    env = {**os.environ, **GIT_ENV}
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )
    stream = result.stdout if result.returncode == 0 else result.stderr
    lines = stream.strip().splitlines()
    answer = json.loads(lines[-1]) if lines else {}
    if result.returncode:
        assert result.stdout == "", "a failure must leave stdout empty"
    return result.returncode, answer, result.stderr


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        env={**os.environ, **GIT_ENV},
    )


def write(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text))


class Crate(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write(
            self.root,
            {"Cargo.toml": CRATE, "Cargo.lock": "version = 4\n", "src/lib.rs": LIB},
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def commit(self, message: str = "commit") -> None:
        if not (self.root / ".git").exists():
            git(self.root, "init", "-q", "-b", "main")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", message)


class InitTest(Crate):
    def test_writes_every_guardrail_then_changes_nothing(self) -> None:
        code, answer, _ = run(self.root, "init")
        self.assertEqual(code, 0)
        self.assertEqual(
            [change[1] for change in answer["changes"]],
            [
                "Cargo.toml",
                "clippy.toml",
                "deny.toml",
                "justfile",
                "lefthook.yml",
                "scripts/rust_guard.py",
                "AGENTS.md",
            ],
        )
        lints = tomllib.loads((self.root / "Cargo.toml").read_text())["lints"]
        self.assertEqual(lints["rust"]["unsafe_code"], "forbid")
        self.assertEqual(lints["clippy"]["unwrap_used"], "deny")
        self.assertIn(
            "<!-- rust-guard:start -->", (self.root / "AGENTS.md").read_text()
        )
        self.assertEqual(run(self.root, "init"), (0, {"ok": True}, ""))

    def test_dry_run_writes_nothing(self) -> None:
        before = sorted(path.name for path in self.root.iterdir())
        code, answer, _ = run(self.root, "init", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn(["update", "Cargo.toml"], answer["changes"])
        self.assertEqual(sorted(path.name for path in self.root.iterdir()), before)

    def test_keeps_existing_agents_text_and_refreshes_its_section(self) -> None:
        write(self.root, {"AGENTS.md": "# Demo\n\nProject rules.\n"})
        run(self.root, "init")
        text = (self.root / "AGENTS.md").read_text()
        self.assertTrue(text.startswith("# Demo\n\nProject rules.\n"))
        stale = text.replace("Run `just check`", "Run something else")
        (self.root / "AGENTS.md").write_text(stale)
        code, answer, _ = run(self.root, "init")
        self.assertEqual((code, answer["changes"]), (0, [["update", "AGENTS.md"]]))
        self.assertEqual((self.root / "AGENTS.md").read_text(), text)

    def test_refuses_a_justfile_without_check_and_writes_nothing(self) -> None:
        write(self.root, {"justfile": "build:\n    cargo build\n"})
        code, answer, _ = run(self.root, "init")
        self.assertEqual(code, 1)
        self.assertIn("no `check` recipe", answer["errors"][0])
        self.assertFalse((self.root / "clippy.toml").exists())

    def test_workspace_members_inherit_the_profile(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": '[workspace]\nmembers = ["crates/*"]\nresolver = "3"\n',
                "crates/a/Cargo.toml": CRATE,
                "crates/b/Cargo.toml": CRATE.replace("demo", "other")
                + "\n[lints]\nworkspace = true\n",
            },
        )
        code, answer, _ = run(self.root, "init")
        self.assertEqual(code, 0)
        self.assertIn(["update", "crates/a/Cargo.toml"], answer["changes"])
        self.assertNotIn(["update", "crates/b/Cargo.toml"], answer["changes"])
        root = tomllib.loads((self.root / "Cargo.toml").read_text())
        self.assertEqual(root["workspace"]["lints"]["clippy"]["panic"], "deny")
        member = tomllib.loads((self.root / "crates/a/Cargo.toml").read_text())
        self.assertEqual(member["lints"], {"workspace": True})

    def test_no_manifest_is_a_usage_error(self) -> None:
        code, answer, _ = run(self.root, "init", "src")
        self.assertEqual(code, 2)
        self.assertIn("has no Cargo.toml", answer["errors"][0])


class AuditTest(Crate):
    def test_lists_missing_lints_and_files(self) -> None:
        code, answer, _ = run(self.root, "audit")
        self.assertEqual(code, 0)
        manifest = answer["manifests"][0]
        self.assertIn("unsafe_code", manifest["missing"])
        self.assertIn("clippy::unwrap_used", manifest["missing"])
        self.assertFalse(answer["files"]["clippy.toml"])
        run(self.root, "init")
        code, answer, _ = run(self.root, "audit")
        self.assertEqual(answer["manifests"][0]["missing"], [])
        self.assertTrue(all(answer["files"].values()))

    def test_flags_a_member_that_does_not_inherit(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": '[workspace]\nmembers = ["crates/a"]\n',
                "crates/a/Cargo.toml": CRATE,
            },
        )
        code, answer, _ = run(self.root, "audit")
        self.assertEqual(code, 0)
        self.assertEqual(answer["manifests"][0]["inherits"], False)

    def test_counts_one_finding_per_location(self) -> None:
        spec = importlib.util.spec_from_file_location("rust_guard", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        finding = {
            "reason": "compiler-message",
            "message": {
                "code": {"code": "clippy::unwrap_used"},
                "spans": [{"file_name": "src/lib.rs", "line_start": 3}],
            },
        }
        stream = "\n".join(
            json.dumps(item)
            for item in (finding, finding, {"reason": "build-finished"})
        )
        self.assertEqual(module.count_findings(stream), {"unwrap_used": 1})


class DiffTest(Crate):
    def setUp(self) -> None:
        super().setUp()
        self.commit("start")

    def test_clean_change_passes(self) -> None:
        write(
            self.root,
            {
                "src/lib.rs": LIB.replace(
                    "a.checked_add(b)", "a.checked_add(b).or(None)"
                )
            },
        )
        self.assertEqual(
            run(self.root, "diff", "--base", "HEAD"), (0, {"ok": True}, "")
        )

    def test_lists_exceptions_and_fails_until_report(self) -> None:
        changed = LIB.replace(
            "pub fn add",
            "#[allow(dead_code)]\n// TODO tidy\npub unsafe fn raw() {}\n\npub fn add",
        ).replace("        assert_eq!(add(1, 2), Some(3));\n", "")
        changed = changed.replace(
            "    #[test]\n    fn adds", "    #[test]\n    #[ignore]\n    fn adds"
        )
        write(
            self.root,
            {
                "src/lib.rs": changed,
                "Cargo.toml": CRATE + 'serde = "1"\n',
                "clippy.toml": 'msrv = "1.85"\n',
            },
        )
        code, answer, _ = run(self.root, "diff", "--base", "HEAD")
        self.assertEqual(code, 1)
        kinds = [exception[0] for exception in answer["exceptions"]]
        for kind in (
            "allow",
            "todo",
            "unsafe",
            "ignore",
            "dependency",
            "protected",
            "assertions_removed",
        ):
            self.assertIn(kind, kinds)
        code, reported, _ = run(self.root, "diff", "--base", "HEAD", "--report")
        self.assertEqual(code, 0)
        self.assertEqual(reported["exceptions"], answer["exceptions"])

    def test_a_removed_test_is_an_exception(self) -> None:
        write(self.root, {"src/lib.rs": LIB.split("#[cfg(test)]")[0]})
        code, answer, _ = run(self.root, "diff", "--base", "HEAD")
        self.assertEqual(code, 1)
        self.assertIn(
            ["tests_removed", ".", "1 fewer test functions"], answer["exceptions"]
        )

    def test_lint_edit_names_each_setting(self) -> None:
        run(self.root, "init")
        self.commit("guardrails")
        manifest = (
            (self.root / "Cargo.toml")
            .read_text()
            .replace('unwrap_used = "deny"', 'unwrap_used = "warn"')
        )
        (self.root / "Cargo.toml").write_text(manifest)
        code, answer, _ = run(self.root, "diff", "--base", "HEAD")
        self.assertEqual(code, 1)
        self.assertIn(
            ["lints", "Cargo.toml", "lints.clippy.unwrap_used: deny -> warn"],
            answer["exceptions"],
        )

    def test_ratchet_flags_new_unwrap_outside_tests_only(self) -> None:
        changed = LIB.replace(
            "a.checked_add(b)", "Some(a.checked_add(b).unwrap())"
        ).replace(
            "assert_eq!(add(1, 2), Some(3));", "assert_eq!(add(1, 2).unwrap(), 3);"
        )
        write(self.root, {"src/lib.rs": changed})
        code, answer, _ = run(self.root, "diff", "--base", "HEAD")
        self.assertEqual(code, 1)
        flagged = [
            exception
            for exception in answer["exceptions"]
            if exception[0] == "unwrap_used"
        ]
        self.assertEqual([exception[1] for exception in flagged], ["src/lib.rs:2"])

    def test_ratchet_stays_quiet_when_the_lint_is_denied(self) -> None:
        run(self.root, "init")
        self.commit("guardrails")
        write(
            self.root,
            {
                "src/lib.rs": LIB.replace(
                    "a.checked_add(b)", "Some(a.checked_add(b).unwrap())"
                )
            },
        )
        self.assertEqual(
            run(self.root, "diff", "--base", "HEAD"), (0, {"ok": True}, "")
        )

    def test_staged_checks_the_index_only(self) -> None:
        write(self.root, {"src/extra.rs": "pub fn f() { unsafe {} }\n"})
        self.assertEqual(run(self.root, "diff", "--staged"), (0, {"ok": True}, ""))
        git(self.root, "add", "src/extra.rs")
        code, answer, _ = run(self.root, "diff", "--staged")
        self.assertEqual(code, 1)
        self.assertEqual(answer["exceptions"][0][:2], ["unsafe", "src/extra.rs:1"])

    def test_untracked_files_count_as_added(self) -> None:
        write(
            self.root,
            {
                "src/new.rs": '#[expect(clippy::panic, reason = "demo")]\npub fn f() {}\n'
            },
        )
        code, answer, _ = run(self.root, "diff", "--base", "HEAD")
        self.assertEqual(code, 1)
        self.assertEqual(answer["exceptions"][0][:2], ["expect", "src/new.rs:1"])

    def test_counts_new_clones_as_notes(self) -> None:
        write(
            self.root,
            {
                "src/lib.rs": LIB
                + "\npub fn dup(v: &Vec<u8>) -> Vec<u8> {\n    v.clone()\n}\n"
            },
        )
        code, answer, _ = run(self.root, "diff", "--base", "HEAD")
        self.assertEqual(code, 0)
        self.assertEqual(answer["notes"][0][:2], ["clone", "."])


if __name__ == "__main__":
    unittest.main()
