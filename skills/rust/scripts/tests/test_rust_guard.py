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


def run(
    cwd: Path, *args: str, env: dict[str, str] | None = None, script: Path = SCRIPT
) -> tuple[int, dict, str]:
    """Run the script; return its exit code, its JSON answer, and stderr."""
    env = {**os.environ, **GIT_ENV, **(env or {})}
    result = subprocess.run(
        [sys.executable, str(script), *args],
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
        self.assertIn("does not run the whole gate", answer["errors"][0])
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
        sys.modules["rust_guard"] = module
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
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))

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
        code, answer, _ = run(self.root, "diff")
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
        code, reported, _ = run(self.root, "diff", "--report")
        self.assertEqual(code, 0)
        self.assertEqual(reported["exceptions"], answer["exceptions"])

    def test_a_removed_test_is_an_exception(self) -> None:
        write(self.root, {"src/lib.rs": LIB.split("#[cfg(test)]")[0]})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn(["tests_removed", ".", "adds"], answer["exceptions"])

    def test_lint_edit_names_each_setting(self) -> None:
        run(self.root, "init")
        self.commit("guardrails")
        manifest = (
            (self.root / "Cargo.toml")
            .read_text()
            .replace('unwrap_used = "deny"', 'unwrap_used = "warn"')
        )
        (self.root / "Cargo.toml").write_text(manifest)
        code, answer, _ = run(self.root, "diff")
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
        code, answer, _ = run(self.root, "diff")
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
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))

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
        code, answer, _ = run(self.root, "diff")
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
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 0)
        self.assertEqual(answer["notes"][0][:2], ["clone", "."])


def kinds(answer: dict) -> list[str]:
    return [exception[0] for exception in answer.get("exceptions", [])]


class RegressionTest(Crate):
    """Cases the first council review reproduced against real crates."""

    def setUp(self) -> None:
        super().setUp()
        self.commit("start")

    def guarded(self) -> None:
        run(self.root, "init")
        self.commit("guardrails")

    def test_a_committed_approved_exception_stops_counting(self) -> None:
        self.guarded()
        approved = LIB.replace(
            "pub fn add",
            '#[expect(clippy::cast_possible_truncation, reason = "demo")]\npub fn narrow(x: u64) -> u32 {\n    x as u32\n}\n\npub fn add',
        )
        write(self.root, {"src/lib.rs": approved})
        self.assertEqual(run(self.root, "diff")[0], 1)
        self.commit("approved exception")
        write(
            self.root,
            {"src/lib.rs": approved.replace("a.checked_add(b)", "b.checked_add(a)")},
        )
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))
        code, answer, _ = run(self.root, "diff", "--base", "HEAD~1", "--report")
        self.assertEqual((code, kinds(answer)), (0, ["expect"]))

    def test_deleting_a_test_file_names_its_tests(self) -> None:
        write(
            self.root,
            {"tests/it.rs": "#[test]\nfn it_works() {\n    assert!(true);\n}\n"},
        )
        self.commit("integration test")
        (self.root / "tests/it.rs").unlink()
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn(["tests_removed", ".", "it_works"], answer["exceptions"])
        self.assertIn("assertions_removed", kinds(answer))

    def test_renamed_and_nested_guardrails_are_protected(self) -> None:
        write(
            self.root,
            {
                "clippy.toml": 'msrv = "1.85"\n',
                "crates/core/rustfmt.toml": "max_width = 100\n",
            },
        )
        self.commit("configs")
        git(self.root, "mv", "clippy.toml", "clippy.toml.bak")
        write(self.root, {"crates/core/rustfmt.toml": "max_width = 200\n"})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        names = [
            exception[1]
            for exception in answer["exceptions"]
            if exception[0] == "protected"
        ]
        self.assertEqual(names, ["clippy.toml", "crates/core/rustfmt.toml"])

    def test_paths_with_spaces_are_read(self) -> None:
        write(self.root, {"src/new file.rs": "#[test]\nfn t() {}\n"})
        self.commit("spaced")
        write(self.root, {"src/new file.rs": "#[test]\n#[ignore]\nfn t() {}\n"})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(
            (code, answer["exceptions"][0][:2]), (1, ["ignore", "src/new file.rs:2"])
        )

    def test_strings_neither_trigger_nor_hide_a_match(self) -> None:
        changed = LIB.replace(
            "a.checked_add(b)",
            'let _label = "unsafe // not code";\n    let _n: u8 = "https://x".len().try_into().ok()?;\n    "7".parse::<u8>().unwrap().checked_add(a.max(b))',
        )
        write(self.root, {"src/lib.rs": changed})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertEqual(kinds(answer), ["unwrap_used"])

    def test_conditional_attributes_count(self) -> None:
        changed = LIB.replace(
            "    #[test]\n    fn adds",
            '    #[test]\n    #[cfg_attr(not(feature = "slow"), ignore)]\n    fn adds',
        )
        write(self.root, {"src/lib.rs": changed})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["ignore"]))

    def test_editing_a_line_that_already_had_unwrap_adds_nothing(self) -> None:
        base = LIB.replace("a.checked_add(b)", "Some(a.checked_add(b).unwrap())")
        write(self.root, {"src/lib.rs": base})
        self.commit("existing debt")
        write(
            self.root,
            {
                "src/lib.rs": base.replace(
                    "a.checked_add(b).unwrap()", "b.checked_add(a).unwrap()"
                )
            },
        )
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))

    def test_test_scope_ends_at_the_closing_brace(self) -> None:
        changed = (
            "#[cfg(test)]\nuse std::fmt;\n\n#[cfg(test)]\nmod helpers {}\n\n"
            "pub fn first(v: &[u8]) -> u8 {\n    *v.first().unwrap()\n}\n\n"
            '#[test]\nfn uses_unwrap() {\n    assert_eq!(first(&[1]), "1".parse::<u8>().unwrap());\n    todo!();\n}\n'
        )
        write(self.root, {"src/extra.rs": changed})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        flagged = [(exception[0], exception[1]) for exception in answer["exceptions"]]
        self.assertEqual(
            flagged, [("unwrap_used", "src/extra.rs:8"), ("todo", "src/extra.rs:14")]
        )

    def test_a_member_that_skips_workspace_lints_is_flagged(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": '[workspace]\nmembers = ["crates/*"]\n',
                "crates/a/Cargo.toml": CRATE,
                "crates/a/src/lib.rs": LIB,
            },
        )
        (self.root / "src/lib.rs").unlink()
        run(self.root, "init")
        self.commit("workspace")
        write(
            self.root,
            {
                "crates/extra/Cargo.toml": CRATE.replace("demo", "extra"),
                "crates/extra/src/lib.rs": "pub fn f(v: Option<u8>) -> u8 {\n    v.unwrap()\n}\n",
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn(
            [
                "lints",
                "crates/extra/Cargo.toml",
                "member does not set [lints] workspace = true",
            ],
            answer["exceptions"],
        )
        self.assertIn("unwrap_used", kinds(answer))

    def test_priority_and_package_renames_are_exceptions(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": CRATE
                + 'driver = { version = "1", package = "old-driver" }\n\n[lints.clippy]\nall = { level = "deny", priority = -1 }\n'
            },
        )
        self.commit("deps")
        text = (self.root / "Cargo.toml").read_text()
        write(
            self.root,
            {
                "Cargo.toml": text.replace("old-driver", "new-driver").replace(
                    "priority = -1", "priority = 1"
                )
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn(
            ["dependency", "Cargo.toml", "dependencies.driver=new-driver"],
            answer["exceptions"],
        )
        self.assertIn("lints", kinds(answer))


class SetupTest(Crate):
    def test_first_commit_lists_the_setup_then_passes(self) -> None:
        git(self.root, "init", "-q", "-b", "main")
        run(self.root, "init")
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn("protected", kinds(answer))
        self.assertIn("lints", kinds(answer))
        git(self.root, "add", "-A")
        code, answer, _ = run(self.root, "diff", "--staged")
        self.assertEqual(code, 1)
        git(self.root, "commit", "-q", "-m", "setup")
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))

    def fake_cargo(self, stdout: str, code: int) -> dict[str, str]:
        folder = self.root / "bin"
        folder.mkdir()
        (folder / "out.json").write_text(stdout)
        cargo = folder / "cargo"
        cargo.write_text(f"#!/bin/sh\ncat '{folder / 'out.json'}'\nexit {code}\n")
        cargo.chmod(0o755)
        return {"PATH": f"{folder}{os.pathsep}{os.environ['PATH']}"}

    def test_violations_report_every_profile_lint(self) -> None:
        finding = {
            "reason": "compiler-message",
            "message": {
                "code": {"code": "clippy::unwrap_used"},
                "spans": [{"file_name": "src/lib.rs", "line_start": 1}],
            },
        }
        other = {
            **finding,
            "message": {
                **finding["message"],
                "code": {"code": "clippy::let_and_return"},
            },
        }
        stream = "\n".join(
            json.dumps(item)
            for item in (finding, other, {"reason": "build-finished", "success": True})
        )
        code, answer, _ = run(
            self.root, "audit", "--violations", env=self.fake_cargo(stream, 0)
        )
        self.assertEqual(code, 0)
        self.assertEqual(answer["violations"]["unwrap_used"], 1)
        self.assertEqual(answer["violations"]["panic"], 0)
        self.assertNotIn("let_and_return", answer["violations"])

    def test_violations_fail_when_the_build_fails(self) -> None:
        stream = json.dumps({"reason": "build-finished", "success": False})
        code, answer, _ = run(
            self.root, "audit", "--violations", env=self.fake_cargo(stream, 101)
        )
        self.assertEqual(code, 1)
        self.assertIn("Clippy did not finish", answer["errors"][0])

    def test_an_existing_check_recipe_must_run_the_gate(self) -> None:
        write(
            self.root,
            {
                "justfile": "check:\n    cargo fmt --all --check\n\ncheck-all:\n    cargo shear\n"
            },
        )
        code, answer, _ = run(self.root, "init")
        self.assertEqual(code, 1)
        self.assertIn("cargo clippy", answer["errors"][0])
        self.assertNotIn("cargo fmt,", answer["errors"][0])
        self.assertFalse((self.root / "clippy.toml").exists())
        code, answer, _ = run(self.root, "audit")
        self.assertIn(
            "uv run scripts/rust_guard.py diff", answer["check_recipe"]["lacks"]
        )

    def test_init_keeps_a_project_owned_guard_script(self) -> None:
        write(self.root, {"scripts/rust_guard.py": "print('mine')\n"})
        code, answer, _ = run(self.root, "init")
        self.assertEqual(code, 1)
        self.assertIn("is not a copy of this script", answer["errors"][0])
        self.assertEqual(
            (self.root / "scripts/rust_guard.py").read_text(), "print('mine')\n"
        )

    def test_the_project_copy_points_init_and_audit_to_the_skill(self) -> None:
        run(self.root, "init")
        code, answer, _ = run(
            self.root, "audit", script=self.root / "scripts/rust_guard.py"
        )
        self.assertEqual(code, 2)
        self.assertIn("run them from the skill copy", answer["errors"][0])

    def test_crlf_manifests_keep_their_line_endings(self) -> None:
        (self.root / "Cargo.toml").write_bytes(CRATE.replace("\n", "\r\n").encode())
        run(self.root, "init")
        data = (self.root / "Cargo.toml").read_bytes()
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))


class NeonRegressionTest(Crate):
    """Cases the first council review's third seat reproduced."""

    def setUp(self) -> None:
        super().setUp()
        self.commit("start")

    def test_commenting_out_a_test_and_its_assertion_counts_as_removal(self) -> None:
        changed = LIB.replace("    #[test]\n", "    // #[test]\n").replace(
            "        assert_eq!(add(1, 2), Some(3));",
            "        // assert_eq!(add(1, 2), Some(3));",
        )
        write(self.root, {"src/lib.rs": changed})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn(["tests_removed", ".", "adds"], answer["exceptions"])
        self.assertIn("assertions_removed", kinds(answer))

    def test_words_in_comments_strings_and_names_are_not_exceptions(self) -> None:
        changed = LIB.replace(
            "pub fn add",
            "/* never use unsafe here */\npub const CSP: &str = \"script-src 'unsafe-inline'\";\npub enum Status { TODO, Done }\n\npub fn add",
        )
        write(self.root, {"src/lib.rs": changed})
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))

    def test_non_utf8_files_do_not_crash(self) -> None:
        (self.root / "fixture.bin").write_bytes(b"caf\xe9\n")
        self.commit("fixture")
        (self.root / "fixture.bin").write_bytes(b"caf\xe9 \xe9\n")
        self.assertEqual(run(self.root, "diff")[0], 0)


class CliAndWorkspaceTest(Crate):
    def test_help_and_closest_command(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "help", "diff"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage: rust_guard.py diff", result.stdout)
        code, answer, _ = run(self.root, "dift")
        self.assertEqual(code, 2)
        self.assertIn("did you mean 'diff'", answer["errors"][0])

    def test_recursive_member_globs_and_excludes(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": '[workspace]\nmembers = ["crates/**"]\nexclude = ["crates/skip-*"]\n',
                "crates/a/b/Cargo.toml": CRATE,
                "crates/skip-me/Cargo.toml": CRATE.replace("demo", "skipped"),
            },
        )
        code, answer, _ = run(self.root, "audit")
        self.assertEqual(code, 0)
        self.assertEqual(
            [entry["path"] for entry in answer["manifests"]], ["crates/a/b/Cargo.toml"]
        )

    def test_a_quiet_check_recipe_counts(self) -> None:
        recipe = (
            (SCRIPT.parent.parent / "assets" / "justfile")
            .read_text()
            .replace("check:", "@check:")
        )
        write(self.root, {"justfile": recipe})
        code, answer, _ = run(self.root, "audit")
        self.assertEqual((code, answer["check_recipe"]["lacks"]), (0, []))

    def test_an_unclosed_agents_section_fails(self) -> None:
        write(self.root, {"AGENTS.md": "# Demo\n\n<!-- rust-guard:start -->\nold\n"})
        code, answer, _ = run(self.root, "init")
        self.assertEqual(code, 1)
        self.assertIn("without <!-- rust-guard:end -->", answer["errors"][0])


class RoundTwoTest(Crate):
    """Cases the second council round reproduced."""

    def setUp(self) -> None:
        super().setUp()
        self.commit("start")

    def test_a_recipe_that_reports_or_drops_flags_lacks_the_gate(self) -> None:
        recipe = (SCRIPT.parent.parent / "assets" / "justfile").read_text()
        loose = recipe.replace("--workspace ", "").replace(
            "rust_guard.py diff", "rust_guard.py diff --report"
        )
        write(
            self.root,
            {"justfile": loose + "# cargo test --workspace --all-features --locked\n"},
        )
        code, answer, _ = run(self.root, "audit")
        self.assertEqual(code, 0)
        lacks = answer["check_recipe"]["lacks"]
        self.assertIn("uv run scripts/rust_guard.py diff", lacks)
        self.assertIn("cargo test --workspace --all-features --locked", lacks)

    def test_an_existing_lefthook_must_run_the_guard(self) -> None:
        write(
            self.root,
            {
                "lefthook.yml": "pre-commit:\n  commands:\n    fmt:\n      run: cargo fmt --check\n"
            },
        )
        code, answer, _ = run(self.root, "init")
        self.assertEqual(code, 1)
        self.assertIn(
            "no pre-commit command running `rust_guard.py diff --staged`",
            answer["errors"][0],
        )

    def test_a_dot_clippy_toml_is_kept(self) -> None:
        write(self.root, {".clippy.toml": 'msrv = "1.85"\n'})
        run(self.root, "init")
        self.assertFalse((self.root / "clippy.toml").exists())

    def test_a_split_or_broadened_attribute_is_new(self) -> None:
        base = LIB.replace(
            "pub fn add",
            '#[expect(clippy::unwrap_used, reason = "demo")]\npub fn add',
        )
        write(self.root, {"src/lib.rs": base})
        self.commit("existing expect")
        broadened = base.replace(
            "#[expect(clippy::unwrap_used,",
            "#[expect(\n    clippy::unwrap_used,\n    clippy::cast_possible_truncation,",
        ).replace(
            "    #[test]\n    fn adds",
            '    #[test]\n    #[cfg_attr(\n        not(feature = "slow"),\n        ignore\n    )]\n    fn adds',
        )
        write(self.root, {"src/lib.rs": broadened})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertEqual(sorted(kinds(answer)), ["expect", "ignore"])
        moved = base.replace("pub fn add", "\n\npub fn add")
        write(self.root, {"src/lib.rs": moved})
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))

    def test_two_unwraps_on_one_line_count_twice(self) -> None:
        base = LIB.replace(
            "a.checked_add(b)", "Some(Some(a).unwrap() + Some(b).unwrap_or_default())"
        )
        write(self.root, {"src/lib.rs": base})
        self.commit("one unwrap")
        write(
            self.root, {"src/lib.rs": base.replace(".unwrap_or_default()", ".unwrap()")}
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["unwrap_used"]))

    def test_dropping_a_test_module_or_test_discovery_is_an_exception(self) -> None:
        write(
            self.root,
            {
                "src/lib.rs": LIB.split("#[cfg(test)]")[0]
                + "#[cfg(test)]\nmod tests;\n",
                "src/tests.rs": "#[test]\nfn t() {}\n",
            },
        )
        self.commit("external tests")
        write(
            self.root,
            {
                "src/lib.rs": LIB.split("#[cfg(test)]")[0],
                "Cargo.toml": CRATE.replace(
                    'edition = "2024"', 'edition = "2024"\nautotests = false'
                ),
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn("test_module_removed", kinds(answer))
        self.assertIn(
            ["test_discovery", "Cargo.toml", "package.autotests changed"],
            answer["exceptions"],
        )

    def test_a_test_only_module_file_is_test_code(self) -> None:
        write(
            self.root,
            {
                "src/lib.rs": LIB + "\n#[cfg(test)]\nmod helpers;\n",
                "src/helpers.rs": "pub fn one() -> u8 {\n    1\n}\n",
            },
        )
        self.commit("helpers")
        write(
            self.root,
            {"src/helpers.rs": 'pub fn one() -> u8 {\n    "1".parse().unwrap()\n}\n'},
        )
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))

    def test_staged_mode_reads_lints_from_the_index(self) -> None:
        write(
            self.root,
            {
                "src/lib.rs": LIB.replace(
                    "a.checked_add(b)", "Some(a.checked_add(b).unwrap())"
                )
            },
        )
        git(self.root, "add", "src/lib.rs")
        write(
            self.root,
            {"Cargo.toml": CRATE + '\n[lints.clippy]\nunwrap_used = "deny"\n'},
        )
        code, answer, _ = run(self.root, "diff", "--staged")
        self.assertEqual((code, kinds(answer)), (1, ["unwrap_used"]))

    def test_pr_report_ignores_changes_made_on_the_base_after_the_fork(self) -> None:
        git(self.root, "checkout", "-q", "-b", "feature")
        write(self.root, {"README.md": "docs\n"})
        self.commit("docs")
        git(self.root, "checkout", "-q", "main")
        write(
            self.root,
            {
                "src/lib.rs": LIB.replace(
                    "    #[test]\n    fn adds",
                    "    #[test]\n    fn more() {}\n\n    #[test]\n    fn adds",
                )
            },
        )
        self.commit("main grows a test")
        git(self.root, "checkout", "-q", "feature")
        code, answer, _ = run(self.root, "diff", "--base", "main", "--report")
        self.assertEqual((code, answer), (0, {"ok": True}))

    def test_joining_an_existing_crate_to_the_workspace_checks_it(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": '[workspace]\nmembers = ["crates/a"]\nexclude = ["crates/b"]\n\n[workspace.lints.clippy]\nunwrap_used = "deny"\n',
                "crates/a/Cargo.toml": CRATE + "\n[lints]\nworkspace = true\n",
                "crates/b/Cargo.toml": CRATE.replace("demo", "bee"),
            },
        )
        (self.root / "src/lib.rs").unlink()
        self.commit("workspace")
        write(
            self.root,
            {
                "Cargo.toml": (self.root / "Cargo.toml")
                .read_text()
                .replace(
                    'members = ["crates/a"]\nexclude = ["crates/b"]',
                    'members = ["crates/a", "crates/b"]',
                )
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn(
            [
                "lints",
                "crates/b/Cargo.toml",
                "member does not set [lints] workspace = true",
            ],
            answer["exceptions"],
        )

    def test_other_ci_files_are_protected(self) -> None:
        write(self.root, {".gitlab-ci.yml": "test:\n  script: just check\n"})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(
            (code, answer["exceptions"][0][:2]), (1, ["protected", ".gitlab-ci.yml"])
        )

    def test_help_wins_over_a_typo(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "typo", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage: rust_guard.py", result.stdout)

    def test_the_project_copy_init_names_the_skill_copy(self) -> None:
        run(self.root, "init")
        code, answer, _ = run(
            self.root, "init", script=self.root / "scripts/rust_guard.py"
        )
        self.assertEqual(code, 2)
        self.assertIn("run them from the skill copy", answer["errors"][0])


class OpusRoundTwoTest(Crate):
    def setUp(self) -> None:
        super().setUp()
        self.commit("start")

    def test_a_changed_unsafe_line_is_new_and_a_moved_one_is_not(self) -> None:
        base = LIB.replace(
            "pub fn add",
            "pub fn raw(p: *const u8) -> u8 {\n    unsafe { *p }\n}\n\npub fn add",
        )
        write(self.root, {"src/lib.rs": base})
        self.commit("existing unsafe")
        write(
            self.root,
            {"src/lib.rs": base.replace("unsafe { *p }", "unsafe { *p.add(100) }")},
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["unsafe"]))
        moved = base.replace("pub fn raw", "\n// moved\npub fn raw")
        write(self.root, {"src/lib.rs": moved})
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))

    def test_a_cfg_that_turns_a_test_off_is_an_exception(self) -> None:
        write(
            self.root,
            {
                "src/lib.rs": LIB.replace(
                    "    #[test]\n    fn adds",
                    "    #[cfg(any())]\n    #[test]\n    fn adds",
                )
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["tests_disabled"]))

    def test_a_member_created_with_inheritance_is_not_a_lint_change(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": '[workspace]\nmembers = ["crates/*"]\n\n[workspace.lints.clippy]\npanic = "deny"\n'
            },
        )
        (self.root / "src/lib.rs").unlink()
        self.commit("workspace")
        write(
            self.root,
            {
                "crates/x/Cargo.toml": CRATE.replace("demo", "x")
                + "\n[lints]\nworkspace = true\n",
                "crates/x/src/lib.rs": "pub fn f() {}\n",
            },
        )
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))


class LayoutTest(Crate):
    def test_dot_member_does_not_crash(self) -> None:
        write(self.root, {"Cargo.toml": CRATE + '\n[workspace]\nmembers = ["."]\n'})
        code, answer, _ = run(self.root, "audit")
        self.assertEqual(
            (code, [entry["path"] for entry in answer["manifests"]]),
            (0, ["Cargo.toml"]),
        )

    def test_a_nested_crate_gets_no_lefthook_file_and_a_note(self) -> None:
        git(self.root, "init", "-q", "-b", "main")
        nested = self.root / "app"
        write(
            nested,
            {"Cargo.toml": CRATE, "Cargo.lock": "version = 4\n", "src/lib.rs": LIB},
        )
        code, answer, _ = run(nested, "init")
        self.assertEqual(code, 0)
        self.assertFalse((nested / "lefthook.yml").exists())
        self.assertIn("root: app/", answer["notes"][0])

    def test_audit_reports_whether_tests_may_panic(self) -> None:
        self.assertFalse(run(self.root, "audit")[1]["tests_may_panic"])
        write(self.root, {"clippy.toml": 'msrv = "1.85"\n'})
        self.assertFalse(run(self.root, "audit")[1]["tests_may_panic"])
        run(self.root, "init")
        (self.root / "clippy.toml").unlink()
        run(self.root, "init")
        self.assertTrue(run(self.root, "audit")[1]["tests_may_panic"])


class NeonRoundTwoTest(Crate):
    def setUp(self) -> None:
        super().setUp()
        self.commit("start")

    def test_a_quote_in_a_block_comment_hides_nothing(self) -> None:
        changed = LIB.replace("a.checked_add(b)", '/* " */ Some(Some(a).unwrap() + b)')
        write(self.root, {"src/lib.rs": changed})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["unwrap_used"]))

    def test_a_quoted_issue_link_counts(self) -> None:
        changed = LIB.replace(
            "pub fn add", '// TODO: see "https://example.com/issues/1"\npub fn add'
        )
        write(self.root, {"src/lib.rs": changed})
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))

    def test_bracket_and_brace_macros_count(self) -> None:
        changed = LIB.replace(
            "a.checked_add(b)", 'if a == 0 { todo!{} } else { panic!["boom"] }'
        )
        write(self.root, {"src/lib.rs": changed})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, sorted(kinds(answer))), (1, ["panic", "todo"]))

    def test_editing_a_line_keeps_its_existing_todo(self) -> None:
        base = LIB.replace("a.checked_add(b)", "a.checked_add(b) // TODO tidy")
        write(self.root, {"src/lib.rs": base})
        self.commit("existing todo")
        write(
            self.root,
            {"src/lib.rs": base.replace("a.checked_add(b)", "b.checked_add(a)")},
        )
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))

    def test_an_inner_cfg_test_file_is_test_code(self) -> None:
        write(
            self.root,
            {
                "src/fixtures.rs": '#![cfg(test)]\n\npub fn one() -> u8 {\n    "1".parse().unwrap()\n}\n'
            },
        )
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))

    def test_the_failure_message_names_the_approval_steps(self) -> None:
        write(self.root, {"src/extra.rs": "pub unsafe fn f() {}\n"})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn("commit the change", answer["errors"][0])


class NeonAuditTest(Crate):
    def test_rustc_reports_unsafe_op_in_unsafe_fn_as_e0133(self) -> None:
        spec = importlib.util.spec_from_file_location("rust_guard_e0133", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules["rust_guard_e0133"] = module
        spec.loader.exec_module(module)
        finding = {
            "reason": "compiler-message",
            "message": {
                "code": {"code": "E0133"},
                "level": "warning",
                "spans": [{"file_name": "src/lib.rs", "line_start": 2}],
            },
        }
        self.assertEqual(
            module.count_findings(json.dumps(finding)), {"unsafe_op_in_unsafe_fn": 1}
        )

    def test_excluding_a_folder_excludes_crates_below_it(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": '[workspace]\nmembers = ["crates/**"]\nexclude = ["crates/skip"]\n',
                "crates/a/Cargo.toml": CRATE,
                "crates/skip/sub/Cargo.toml": CRATE.replace("demo", "sub"),
            },
        )
        code, answer, _ = run(self.root, "audit")
        self.assertEqual(code, 0)
        self.assertEqual(
            [entry["path"] for entry in answer["manifests"]], ["crates/a/Cargo.toml"]
        )

    def test_help_after_a_global_flag(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-v", "help", "diff"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage: rust_guard.py diff", result.stdout)


class RoundThreeTest(Crate):
    def setUp(self) -> None:
        super().setUp()
        self.commit("start")

    def test_an_error_ignoring_guard_step_lacks_the_gate(self) -> None:
        recipe = (SCRIPT.parent.parent / "assets" / "justfile").read_text()
        write(
            self.root,
            {
                "justfile": recipe.replace(
                    "    uv run scripts/rust_guard.py diff",
                    "    -uv run scripts/rust_guard.py diff",
                )
            },
        )
        code, answer, _ = run(self.root, "audit")
        self.assertEqual(
            (code, answer["check_recipe"]["lacks"]),
            (0, ["uv run scripts/rust_guard.py diff"]),
        )

    def test_the_hook_audit_needs_a_blocking_pre_commit_command(self) -> None:
        self.assertFalse(run(self.root, "audit")[1]["hook_runs_guard"])
        write(
            self.root,
            {
                "lefthook.yml": "pre-push:\n  commands:\n    g:\n      run: uv run scripts/rust_guard.py diff --staged\n"
            },
        )
        self.assertFalse(run(self.root, "audit")[1]["hook_runs_guard"])
        write(
            self.root,
            {
                "lefthook.yml": (
                    SCRIPT.parent.parent / "assets" / "lefthook.yml"
                ).read_text()
            },
        )
        self.assertTrue(run(self.root, "audit")[1]["hook_runs_guard"])

    def test_the_pr_list_reads_commits_not_the_working_tree(self) -> None:
        git(self.root, "checkout", "-q", "-b", "feature")
        write(
            self.root,
            {"src/lib.rs": LIB.replace("pub fn add", "// TODO tidy\npub fn add")},
        )
        self.commit("todo")
        write(self.root, {"src/lib.rs": LIB})
        code, answer, _ = run(self.root, "diff", "--base", "main", "--report")
        self.assertEqual((code, kinds(answer)), (0, ["todo"]))

    def test_moving_an_expect_to_another_item_is_new(self) -> None:
        base = LIB.replace(
            "pub fn add",
            '#[expect(clippy::expect_used, reason = "embedded")]\npub fn load() -> u8 {\n    1\n}\n\npub fn parse() -> u8 {\n    2\n}\n\npub fn add',
        )
        write(self.root, {"src/lib.rs": base})
        self.commit("approved expect")
        moved = base.replace(
            '#[expect(clippy::expect_used, reason = "embedded")]\npub fn load',
            "pub fn load",
        ).replace(
            "pub fn parse",
            '#[expect(clippy::expect_used, reason = "embedded")]\npub fn parse',
        )
        write(self.root, {"src/lib.rs": moved})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["expect"]))

    def test_an_inner_cfg_that_switches_a_test_file_off(self) -> None:
        write(
            self.root, {"tests/it.rs": "#[test]\nfn works() {\n    assert!(true);\n}\n"}
        )
        self.commit("integration")
        write(
            self.root,
            {
                "tests/it.rs": "#![cfg(any())]\n\n#[test]\nfn works() {\n    assert!(true);\n}\n"
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["tests_disabled"]))

    def test_removing_a_member_is_an_exception(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": '[workspace]\nmembers = ["crates/a", "crates/b"]\n',
                "crates/a/Cargo.toml": CRATE,
                "crates/b/Cargo.toml": CRATE.replace("demo", "bee"),
            },
        )
        self.commit("two members")
        write(self.root, {"Cargo.toml": '[workspace]\nmembers = ["crates/a"]\n'})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn(
            ["members_removed", "Cargo.toml", "crates/b"], answer["exceptions"]
        )


class RoundThreeAuditTest(Crate):
    def test_an_unsafe_code_override_counts_against_forbid(self) -> None:
        write(
            self.root,
            {
                "src/ffi.rs": '#[allow(unsafe_code, reason = "legacy ffi")]\npub fn f() {}\n'
            },
        )
        folder = self.root / "bin"
        folder.mkdir()
        (folder / "out.json").write_text(
            json.dumps({"reason": "build-finished", "success": True})
        )
        cargo = folder / "cargo"
        cargo.write_text(f"#!/bin/sh\ncat '{folder / 'out.json'}'\n")
        cargo.chmod(0o755)
        env = {"PATH": f"{folder}{os.pathsep}{os.environ['PATH']}"}
        code, answer, _ = run(self.root, "audit", "--violations", env=env)
        self.assertEqual((code, answer["violations"]["unsafe_code"]), (0, 1))


class OpusRoundThreeTest(Crate):
    def setUp(self) -> None:
        super().setUp()
        self.commit("start")

    def test_switching_off_a_test_module_is_an_exception(self) -> None:
        write(self.root, {"src/lib.rs": LIB.replace("#[cfg(test)]", "#[cfg(any())]")})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn("tests_disabled", kinds(answer))

    def test_doctests_switched_off_or_emptied_are_exceptions(self) -> None:
        documented = LIB.replace(
            "pub fn add",
            "/// ```\n/// assert_eq!(demo::add(1, 1), Some(2));\n/// ```\npub fn add",
        )
        write(self.root, {"src/lib.rs": documented})
        self.commit("doctest")
        write(
            self.root,
            {
                "src/lib.rs": documented.replace(
                    "/// ```\n/// assert_eq",
                    "/// ```ignore\n/// let _ = 1; // assert_eq",
                )
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn("doctest_disabled", kinds(answer))
        self.assertIn("assertions_removed", kinds(answer))

    def test_an_edit_inside_a_multi_line_unsafe_block_is_new(self) -> None:
        base = LIB.replace(
            "pub fn add",
            "pub fn raw(p: *const u8) -> u8 {\n    unsafe {\n        *p\n    }\n}\n\npub fn add",
        )
        write(self.root, {"src/lib.rs": base})
        self.commit("existing unsafe block")
        write(
            self.root,
            {"src/lib.rs": base.replace("        *p\n", "        *p.add(7)\n")},
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["unsafe"]))

    def test_integration_test_helpers_are_test_code(self) -> None:
        write(
            self.root,
            {
                "tests/it.rs": "#[cfg(test)]\nmod common;\n\n#[test]\nfn works() {\n    assert_eq!(common::one(), 1);\n}\n",
                "tests/common/mod.rs": "pub fn one() -> u8 {\n    1\n}\n",
            },
        )
        self.commit("helpers")
        write(
            self.root,
            {
                "tests/common/mod.rs": 'pub fn one() -> u8 {\n    "1".parse().unwrap()\n}\n'
            },
        )
        self.assertEqual(run(self.root, "diff"), (0, {"ok": True}, ""))

    def test_the_report_shows_the_reason_as_written(self) -> None:
        write(
            self.root,
            {
                "src/extra.rs": '#[expect(clippy::panic, reason = "demo only")]\npub fn f() {}\n'
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn('reason = "demo only"', answer["exceptions"][0][2])


class NestedHookTest(Crate):
    def test_the_nested_refusal_names_the_root_setting(self) -> None:
        git(self.root, "init", "-q", "-b", "main")
        write(
            self.root,
            {
                "lefthook.yml": "pre-commit:\n  commands:\n    fmt:\n      run: cargo fmt --check\n"
            },
        )
        nested = self.root / "app"
        write(
            nested,
            {"Cargo.toml": CRATE, "Cargo.lock": "version = 4\n", "src/lib.rs": LIB},
        )
        code, answer, _ = run(nested, "init")
        self.assertEqual(code, 1)
        self.assertIn("root: app/", answer["errors"][0])


class NeonRoundThreeTest(Crate):
    def setUp(self) -> None:
        super().setUp()
        self.commit("start")

    def test_a_platform_cfg_on_a_use_inside_tests_is_not_disabling(self) -> None:
        write(
            self.root,
            {
                "src/lib.rs": LIB.replace(
                    "    use super::*;\n",
                    "    use super::*;\n    #[cfg(unix)]\n    use std::os::unix::ffi::OsStrExt;\n",
                )
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, answer), (0, {"ok": True}))

    def test_a_platform_cfg_on_a_test_is_disabling(self) -> None:
        write(
            self.root,
            {
                "src/lib.rs": LIB.replace(
                    "    #[test]\n", "    #[cfg(windows)]\n    #[test]\n"
                )
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["tests_disabled"]))

    def test_switching_off_binary_tests_is_an_exception(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": CRATE
                + '\n[[bin]]\nname = "demo"\npath = "src/main.rs"\n',
                "src/main.rs": "fn main() {}\n",
            },
        )
        self.commit("binary")
        write(
            self.root,
            {
                "Cargo.toml": CRATE
                + '\n[[bin]]\nname = "demo"\npath = "src/main.rs"\ntest = false\n'
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn(
            ["test_discovery", "Cargo.toml", "[[bin]] changed"], answer["exceptions"]
        )
        write(
            self.root,
            {
                "Cargo.toml": CRATE.replace(
                    'edition = "2024"', 'edition = "2024"\nautobins = false'
                )
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertTrue(
            any("package.autobins" in entry[2] for entry in answer["exceptions"])
        )

    def test_adding_a_clean_member_leaves_a_legacy_member_alone(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": '[workspace]\nmembers = ["crates/old"]\n\n[workspace.lints.clippy]\nunwrap_used = "deny"\n',
                "crates/old/Cargo.toml": CRATE,
            },
        )
        (self.root / "src/lib.rs").unlink()
        self.commit("legacy workspace")
        write(
            self.root,
            {
                "Cargo.toml": (self.root / "Cargo.toml")
                .read_text()
                .replace('["crates/old"]', '["crates/old", "crates/new"]'),
                "crates/new/Cargo.toml": CRATE.replace("demo", "fresh")
                + "\n[lints]\nworkspace = true\n",
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, answer), (0, {"ok": True}))

    def test_the_nested_note_runs_the_guard_from_the_root(self) -> None:
        nested = self.root / "app"
        write(
            nested,
            {"Cargo.toml": CRATE, "Cargo.lock": "version = 4\n", "src/lib.rs": LIB},
        )
        code, answer, _ = run(nested, "init")
        self.assertEqual(code, 0)
        note = answer["notes"][0]
        self.assertIn("uv run app/scripts/rust_guard.py diff --staged", note)
        self.assertIn("with no `root:`", note)
        self.assertIn("root: app/", note)

    def test_audit_finds_alternate_file_names(self) -> None:
        write(
            self.root,
            {
                ".clippy.toml": "allow-unwrap-in-tests = true\n",
                "lefthook.yaml": "pre-commit:\n  commands: {}\n",
            },
        )
        files = run(self.root, "audit")[1]["files"]
        self.assertTrue(files["clippy.toml"])
        self.assertTrue(files["lefthook.yml"])


WORKSPACE = '[workspace]\nmembers = ["crates/*"]\n\n[workspace.lints.clippy]\nunwrap_used = "deny"\n'
MEMBER = CRATE + "\n[lints]\nworkspace = true\n"


class AstraRoundFourTest(Crate):
    def setUp(self) -> None:
        super().setUp()
        self.commit("start")

    def workspace(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": WORKSPACE,
                "crates/alpha/Cargo.toml": MEMBER,
                "crates/beta/Cargo.toml": MEMBER.replace("demo", "beta"),
            },
        )
        (self.root / "src/lib.rs").unlink()
        self.commit("workspace")

    def test_excluding_a_member_removes_it(self) -> None:
        self.workspace()
        write(
            self.root,
            {
                "Cargo.toml": WORKSPACE.replace(
                    "]\n\n", ']\nexclude = ["crates/beta"]\n\n', 1
                )
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual(code, 1)
        self.assertIn(
            ["members_removed", "Cargo.toml", "crates/beta"], answer["exceptions"]
        )

    def test_a_new_crate_under_exclude_is_not_a_member(self) -> None:
        self.workspace()
        write(
            self.root,
            {
                "Cargo.toml": WORKSPACE.replace(
                    "]\n\n", ']\nexclude = ["crates/sample"]\n\n', 1
                ),
                "crates/sample/Cargo.toml": CRATE.replace("demo", "sample"),
            },
        )
        self.assertEqual(run(self.root, "diff")[:2], (0, {"ok": True}))

    def test_the_pr_list_ignores_a_renamed_folder_in_the_working_tree(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": '[workspace]\nmembers = ["a"]\n\n[workspace.lints.clippy]\nunwrap_used = "deny"\n',
                "a/Cargo.toml": MEMBER,
                "b/Cargo.toml": CRATE.replace("demo", "bee"),
            },
        )
        (self.root / "src/lib.rs").unlink()
        self.commit("workspace")
        git(self.root, "checkout", "-q", "-b", "feature")
        write(
            self.root,
            {
                "Cargo.toml": (self.root / "Cargo.toml")
                .read_text()
                .replace('["a"]', '["a", "b"]')
            },
        )
        self.commit("join b")
        expected = [
            "lints",
            "b/Cargo.toml",
            "member does not set [lints] workspace = true",
        ]
        _, answer, _ = run(self.root, "diff", "--base", "main", "--report")
        self.assertIn(expected, answer["exceptions"])
        (self.root / "b").rename(self.root / "c")
        _, answer, _ = run(self.root, "diff", "--base", "main", "--report")
        self.assertIn(expected, answer["exceptions"])

    def test_a_guard_limited_to_some_files_does_not_count(self) -> None:
        hook = (SCRIPT.parent.parent / "assets" / "lefthook.yml").read_text()
        write(
            self.root,
            {
                "lefthook.yml": hook.replace(
                    "      run: uv run scripts/rust_guard.py diff --staged",
                    '      glob: "*.rs"\n      run: uv run scripts/rust_guard.py diff --staged',
                )
            },
        )
        self.assertIn('glob: "*.rs"', (self.root / "lefthook.yml").read_text())
        self.assertFalse(run(self.root, "audit")[1]["hook_runs_guard"])

    def test_a_platform_cfg_on_a_module_of_tests_is_disabling(self) -> None:
        tests = "mod regression {\n    #[test]\n    fn works() {\n        assert!(true);\n    }\n}\n"
        write(self.root, {"tests/it.rs": tests})
        self.commit("integration")
        write(self.root, {"tests/it.rs": "#[cfg(windows)]\n" + tests})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["tests_disabled"]))

    def test_doctests_count_runnable_blocks(self) -> None:
        example = "/// ```\n/// let _ = demo::add(1, 1);\n/// ```\n"
        documented = LIB.replace("pub fn add", example + "pub fn add")
        write(self.root, {"src/lib.rs": documented})
        self.commit("doctest")
        write(self.root, {"src/lib.rs": LIB})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["doctest_disabled"]))
        output = "/// ```text\n/// demo 0.1.0\n/// ```\n"
        write(
            self.root,
            {"src/lib.rs": documented.replace("pub fn add", output + "pub fn add")},
        )
        self.assertEqual(run(self.root, "diff")[:2], (0, {"ok": True}))


class OpusRoundFourTest(Crate):
    def setUp(self) -> None:
        super().setUp()
        self.commit("start")

    def test_a_new_gated_test_is_not_disabled(self) -> None:
        write(
            self.root,
            {
                "src/lib.rs": LIB.replace(
                    "    #[test]\n    fn adds",
                    "    #[cfg(unix)]\n    #[test]\n    fn on_unix() {\n        assert!(true);\n    }\n\n    #[test]\n    fn adds",
                ),
                "tests/wide.rs": '#![cfg(feature = "wide")]\n\n#[test]\nfn wide() {\n    assert!(true);\n}\n',
            },
        )
        self.assertEqual(run(self.root, "diff")[:2], (0, {"ok": True}))

    def test_a_new_field_keeps_the_approved_expect_on_another(self) -> None:
        shape = (
            "pub struct Config {\n"
            '    #[expect(dead_code, reason = "kept for the wire format")]\n'
            "    reserved: u8,\n"
            "}\n"
        )
        write(self.root, {"src/lib.rs": shape + LIB})
        self.commit("approved expect")
        write(
            self.root,
            {"src/lib.rs": shape.replace("}\n", "    pub port: u16,\n}\n") + LIB},
        )
        self.assertEqual(run(self.root, "diff")[:2], (0, {"ok": True}))

    def test_cfg_test_off_a_module_and_cfg_attr_inner_are_not_disabling(self) -> None:
        write(
            self.root,
            {"src/lib.rs": "#[cfg(test)]\nconst LIMIT: u8 = 3;\n\n" + LIB},
        )
        self.commit("test constant")
        write(
            self.root,
            {"src/lib.rs": "#![cfg_attr(not(test), no_std)]\n\n" + LIB},
        )
        self.assertEqual(run(self.root, "diff")[:2], (0, {"ok": True}))


class RoundFiveTest(Crate):
    def setUp(self) -> None:
        super().setUp()
        self.commit("start")

    def test_switching_a_platform_value_disables_a_test(self) -> None:
        gated = LIB.replace(
            "    #[test]\n", '    #[cfg(target_os = "linux")]\n    #[test]\n'
        )
        write(self.root, {"src/lib.rs": gated})
        self.commit("linux only")
        write(self.root, {"src/lib.rs": gated.replace('"linux"', '"windows"')})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["tests_disabled"]))

    def test_a_skip_on_the_whole_hook_does_not_count(self) -> None:
        hook = (SCRIPT.parent.parent / "assets" / "lefthook.yml").read_text()
        write(
            self.root,
            {
                "lefthook.yml": hook.replace(
                    "pre-commit:\n", "pre-commit:\n  skip:\n    - merge\n", 1
                )
            },
        )
        self.assertIn("  skip:", (self.root / "lefthook.yml").read_text())
        self.assertFalse(run(self.root, "audit")[1]["hook_runs_guard"])

    def test_a_renamed_parent_in_the_working_tree_changes_no_pr_list(self) -> None:
        write(
            self.root,
            {
                "tests/smoke.rs": "#[cfg(test)]\nmod common;\n\n#[test]\nfn smoke() {\n    assert!(common::ready());\n}\n",
                "tests/common/mod.rs": "pub fn ready() -> bool {\n    true\n}\n",
            },
        )
        self.commit("helpers")
        git(self.root, "checkout", "-q", "-b", "feature")
        write(
            self.root,
            {
                "tests/common/mod.rs": "pub fn ready() -> bool {\n    Some(true).unwrap()\n}\n"
            },
        )
        self.commit("helper unwrap")
        self.assertEqual(
            run(self.root, "diff", "--base", "main", "--report")[:2], (0, {"ok": True})
        )
        (self.root / "tests/smoke.rs").rename(self.root / "tests/other.rs")
        self.assertEqual(
            run(self.root, "diff", "--base", "main", "--report")[:2], (0, {"ok": True})
        )

    def test_a_cfg_on_an_out_of_line_module_of_tests_is_disabling(self) -> None:
        write(
            self.root,
            {
                "src/lib.rs": "mod protocol;\n",
                "src/protocol.rs": LIB,
            },
        )
        self.commit("protocol")
        write(self.root, {"src/lib.rs": "#[cfg(windows)]\nmod protocol;\n"})
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["tests_disabled"]))

    def test_moving_a_module_and_its_tests_to_a_file_is_clean(self) -> None:
        write(
            self.root,
            {"src/lib.rs": "mod parse;\npub use parse::add;\n", "src/parse.rs": LIB},
        )
        self.assertEqual(run(self.root, "diff")[:2], (0, {"ok": True}))

    def test_moving_an_approved_expect_to_another_file_keeps_it(self) -> None:
        spare = '#[expect(dead_code, reason = "kept for the next release")]\nfn spare() {}\n'
        write(self.root, {"src/lib.rs": LIB + spare})
        self.commit("approved")
        write(self.root, {"src/lib.rs": "mod extra;\n" + LIB, "src/extra.rs": spare})
        self.assertEqual(run(self.root, "diff")[:2], (0, {"ok": True}))

    def test_renaming_a_member_folder_is_not_a_removal(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": '[workspace]\nmembers = ["crates/cli"]\n\n[workspace.lints.clippy]\nunwrap_used = "deny"\n',
                "crates/cli/Cargo.toml": CRATE + "\n[lints]\nworkspace = true\n",
            },
        )
        (self.root / "src/lib.rs").unlink()
        self.commit("workspace")
        git(self.root, "mv", "crates/cli", "crates/ledger-cli")
        write(
            self.root,
            {
                "Cargo.toml": (self.root / "Cargo.toml")
                .read_text()
                .replace("crates/cli", "crates/ledger-cli")
            },
        )
        self.assertEqual(run(self.root, "diff")[:2], (0, {"ok": True}))

    def test_a_patched_crate_is_a_new_dependency(self) -> None:
        write(
            self.root,
            {
                "Cargo.toml": CRATE
                + '\n[patch.crates-io]\nserde = { path = "../serde" }\n'
            },
        )
        code, answer, _ = run(self.root, "diff")
        self.assertEqual((code, kinds(answer)), (1, ["dependency"]))


if __name__ == "__main__":
    unittest.main()
