"""Run plan_graph.py on wave files written in a temporary plan folder."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "plan_graph.py"


def task(
    brief_id,
    blocked_by=(),
    touches=("src/a.ts",),
    state="todo",
    needs=(),
    executor=None,
):
    block = {
        "id": brief_id,
        "blocked_by": [{"id": blocker, "why": "contract"} for blocker in blocked_by],
        "needs": list(needs),
        "touches": list(touches),
    }
    who = f" · Executor: {executor}" if executor else ""
    return brief(brief_id, block, f"- Kind: feature{who} · State: {state}")


def wave(
    executor: str | None = "agent",
    epic: str | None = "agent",
    status: str = "active",
    version: str | None = "3.0.0",
):
    """The head of a wave file: front matter and the entry of epic E04."""
    lines = ["---", "id: W02", f"status: {status}"]
    lines += [f'skill_version: "{version}"'] if version else []
    lines += [f"executor: {executor}   # agent | human | tbd"] if executor else []
    lines += ["---", "", "# W02: x", "", "### E04: epic → #1"]
    lines += [f"- Executor: {epic}"] if epic else []
    return "\n".join(lines) + "\n\n"


def qa(brief_id, verifies):
    block = {"id": brief_id, "verifies": list(verifies), "needs": []}
    return brief(brief_id, block, "- Kind: qa · State: todo")


def brief(brief_id, block, line):
    return f"#### {brief_id}: title → #1\n{line}\n\n```json\n{json.dumps(block)}\n```\n"


class PlanGraph(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.waves = Path(folder.name)

    def run_on(
        self, *briefs, name="W02-x.md", flags=(), head="# W02\n\n### E04: epic\n\n"
    ):
        path = self.waves / name
        path.write_text(head + "\n".join(briefs))
        return subprocess.run(
            [sys.executable, str(SCRIPT), *flags, str(path)],
            capture_output=True,
            text=True,
            check=False,
        )

    def passes(self, *briefs, head="# W02\n\n### E04: epic\n\n"):
        result = self.run_on(*briefs, head=head)
        self.assertEqual(result.returncode, 0, result.stderr)
        answer = json.loads(result.stdout)
        self.assertEqual(answer["file"], str(self.waves / "W02-x.graph.json"))
        return json.loads(Path(answer["file"]).read_text())

    def fails(self, *briefs, head="# W02\n\n### E04: epic\n\n"):
        result = self.run_on(*briefs, head=head)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(result.stdout, "")
        answer = json.loads(result.stderr.splitlines()[-1])
        self.assertFalse(answer["ok"])
        return " ".join(answer["errors"])

    def test_the_answer_reports_the_longest_chain_and_the_width_of_each_batch(self):
        result = self.run_on(
            task("E04-T01", touches=["src/a.ts"]),
            task("E05-T01", touches=["src/b.ts"]),
            task("E04-T02", blocked_by=["E04-T01"], touches=["src/a.ts"]),
            qa("E04-QA1", ["E04-T01", "E04-T02"]),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        answer = json.loads(result.stdout)
        self.assertEqual(answer["longest_chain"], 3)
        self.assertEqual(answer["widths"], [2, 1, 1])

    def test_batches_follow_the_blockers_and_a_qa_task_gates_only_its_dependents(self):
        answer = self.passes(
            task("E04-T01", touches=["src/a.ts"]),
            task("E05-T01", touches=["src/b.ts"]),
            task("E04-T02", blocked_by=["E04-T01"], touches=["src/a.ts"]),
            qa("E04-QA1", ["E04-T01", "E04-T02"]),
            task("E05-T02", blocked_by=["E04-QA1"], touches=["src/c.ts"]),
        )
        self.assertEqual(
            answer["batches"],
            [["E04-T01", "E05-T01"], ["E04-T02"], ["E04-QA1"], ["E05-T02"]],
        )
        self.assertEqual(answer["gates"], {"E04-QA1": ["E05-T02"]})
        self.assertEqual(answer["wave_file"], "W02-x.md")
        self.assertEqual(answer["nodes"][3]["kind"], "qa")
        self.assertEqual(answer["nodes"][2]["touches"], ["src/a.ts"])
        self.assertIn(
            {"from": "E04-T01", "to": "E04-T02", "why": "contract"}, answer["edges"]
        )
        self.assertIn(
            {"from": "E04-T02", "to": "E04-QA1", "why": "verifies"}, answer["edges"]
        )

    def test_the_graph_file_is_written_once_and_check_fails_when_it_is_stale(self):
        graph_file = self.waves / "W02-x.graph.json"
        dry = self.run_on(task("E04-T01"), flags=["--dry-run"])
        self.assertEqual(
            json.loads(dry.stdout)["changes"], [["write", str(graph_file)]]
        )
        self.assertFalse(graph_file.exists())
        missing = self.run_on(task("E04-T01"), flags=["--check"])
        self.assertEqual(missing.returncode, 1)
        self.assertFalse(graph_file.exists())
        first = json.loads(self.run_on(task("E04-T01")).stdout)
        self.assertEqual(first["changes"], [["write", str(graph_file)]])
        self.assertNotIn("changes", json.loads(self.run_on(task("E04-T01")).stdout))
        self.assertEqual(self.run_on(task("E04-T01"), flags=["--check"]).returncode, 0)
        later = task("E04-T02", blocked_by=["E04-T01"])
        stale = self.run_on(task("E04-T01"), later, flags=["--check"])
        self.assertEqual(stale.returncode, 1)
        answer = json.loads(stale.stderr.splitlines()[-1])
        self.assertEqual(answer["changes"], [["write", str(graph_file)]])
        self.assertIn("does not match the briefs", answer["errors"][0])

    def test_a_qa_task_that_no_task_names_gates_nothing(self):
        answer = self.passes(task("E04-T01"), qa("E04-QA1", ["E04-T01"]))
        self.assertEqual(answer["gates"], {})

    def test_parallel_tasks_with_a_common_path_fail(self):
        errors = self.fails(
            task("E04-T01", touches=["src/auth/**"]),
            task("E04-T02", touches=["src/auth/db.ts"]),
        )
        self.assertIn("E04-T01 and E04-T02 can run at the same time", errors)
        self.passes(
            task("E04-T01", touches=["src/auth/**", "docs/a.md"]),
            task("E04-T02", touches=["src/authz/**", "docs/b.md"]),
        )
        same = self.fails(
            task("E04-T01", touches=["./src/a.ts"]),
            task("E04-T02", touches=["src/a.ts"]),
        )
        self.assertIn("can run at the same time", same)
        self.passes(task("E04-T01", touches=["app/[id]/page.tsx"]))
        glob = self.fails(task("E04-T01", touches=["src/*.ts"]))
        self.assertIn("write each entry as a path or as `dir/**`", glob)

    def test_the_state_comes_from_the_kind_line_only(self):
        mention = task("E04-T01").replace("```json", "- Today: State: done\n\n```json")
        self.assertIn("can run at the same time", self.fails(mention, task("E04-T02")))

    def test_an_unknown_state_and_text_after_the_block_fail(self):
        self.assertIn(
            "has the state 'todo.'", self.fails(task("E04-T01", state="todo."))
        )
        self.passes(task("E04-T01", state="carried→W03"))
        late = task("E04-T01") + "- [ ] a late acceptance item\n"
        self.assertIn("has text after its json block", self.fails(late))
        self.passes(task("E04-T01"), "## Discoveries\n- E04-T01: a finding\n")

    def test_a_level_4_heading_that_is_not_a_brief_fails(self):
        errors = self.fails(task("E04-T01"), "#### E04-TXX: title\n")
        self.assertIn("is not a brief heading", errors)
        unclosed = self.fails(task("E04-T01"), "```json\n")
        self.assertIn("never closes", unclosed)

    def test_a_dropped_qa_task_keeps_its_dropped_targets(self):
        dropped_qa = qa("E04-QA1", ["E04-T01"]).replace("State: todo", "State: dropped")
        self.passes(task("E04-T01", state="dropped"), dropped_qa)

    def test_a_qa_task_of_another_wave_file_gates_and_its_state_counts(self):
        (self.waves / "W01-y.md").write_text(
            qa("E03-QA1", ["E03-T01"]) + task("E03-T02", state="dropped")
        )
        answer = self.passes(task("E04-T01", blocked_by=["E03-QA1"]))
        self.assertEqual(answer["gates"], {"E03-QA1": ["E04-T01"]})
        errors = self.fails(task("E04-T01", blocked_by=["E03-T02"]))
        self.assertIn("which is dropped", errors)
        self.assertIn("a QA task", self.fails(qa("E04-QA1", ["E03-QA1"])))

    def test_a_transitive_blocker_orders_tasks_with_a_common_path(self):
        self.passes(
            task("E04-T01", touches=["src/a.ts"]),
            task("E04-T02", blocked_by=["E04-T01"], touches=["src/b.ts"]),
            task("E04-T03", blocked_by=["E04-T02"], touches=["src/a.ts"]),
        )

    def test_a_done_task_does_not_conflict(self):
        self.passes(task("E04-T01", state="done"), task("E04-T02"))

    def test_a_cycle_fails(self):
        errors = self.fails(
            task("E04-T01", blocked_by=["E04-T02"]),
            task("E04-T02", blocked_by=["E04-T01"]),
        )
        self.assertIn("cycle", errors)

    def test_an_unknown_id_fails_and_an_id_of_another_wave_file_passes(self):
        self.assertIn(
            "names E03-T09", self.fails(task("E04-T01", blocked_by=["E03-T09"]))
        )
        (self.waves / "W01-y.md").write_text(task("E03-T09"))
        self.passes(task("E04-T01", blocked_by=["E03-T09"]))

    def test_a_dropped_blocker_fails(self):
        errors = self.fails(
            task("E04-T01", state="dropped"), task("E04-T02", blocked_by=["E04-T01"])
        )
        self.assertIn("which is dropped", errors)

    def test_a_brief_without_a_valid_block_fails(self):
        self.assertIn(
            "has 0 json blocks", self.fails("#### E04-T01: title\n- Kind: feature\n")
        )
        wrong = brief("E04-T01", {"id": "E04-T01", "touches": []}, "- Kind: feature")
        self.assertIn("exactly the keys", self.fails(wrong))
        need = task("E04-T01", needs=[{"what": "key"}])
        self.assertIn('"needs" each item must be', self.fails(need))

    def test_a_missing_file_is_a_usage_error(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.waves / "none.md")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)

    def hitl(self):
        before = sorted(self.waves.iterdir())
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--hitl", str(self.waves)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(self.waves.iterdir()), before)
        return {each["wave"]: each for each in json.loads(result.stdout)["waves"]}

    def test_a_human_task_blocks_the_wave_until_it_is_done(self):
        human = task("E04-T02", touches=["b"], executor="human")
        (self.waves / "W02-x.md").write_text(
            wave(executor="human", epic="human")
            + task("E04-T01", executor="agent")
            + human
        )
        report = self.hitl()["W02"]
        self.assertFalse(report["agent_ready"])
        self.assertEqual(
            report["unresolved"],
            [{"id": "E04-T02", "executor": "human", "state": "todo"}],
        )
        (self.waves / "W02-x.md").write_text(
            wave(executor="human", epic="human")
            + task("E04-T01", executor="agent")
            + human.replace("State: todo", "State: done")
        )
        self.assertTrue(self.hitl()["W02"]["agent_ready"])

    def test_a_carried_human_task_counts_only_in_its_receiving_wave(self):
        carried = task("E04-T02", executor="human", state="carried→W03")
        (self.waves / "W02-x.md").write_text(
            wave(status="done", executor="human", epic="human") + carried
        )
        receiving = wave(executor="human", epic=None).replace("W02", "W03")
        receiving = receiving.replace("### E04: epic", "### E04 (continued from W02)")
        copy = task("E04-T02", executor="human")
        (self.waves / "W03-y.md").write_text(receiving + copy)
        report = self.hitl()
        self.assertTrue(report["W02"]["agent_ready"])
        self.assertEqual(
            [item["id"] for item in report["W03"]["unresolved"]], ["E04-T02"]
        )
        (self.waves / "W03-y.md").write_text(
            receiving + copy.replace("State: todo", "State: done")
        )
        self.assertTrue(self.hitl()["W03"]["agent_ready"])

    def test_each_tbd_is_unresolved_and_a_legacy_file_reports_unknown(self):
        (self.waves / "W04-z.md").write_text(
            wave(status="proposed", executor="tbd", epic="tbd").replace("W02", "W04")
        )
        (self.waves / "W01-y.md").write_text(
            wave(status="done", executor=None, epic=None, version=None).replace(
                "W02", "W01"
            )
            + task("E04-T01", state="done", executor="agent")
        )
        report = self.hitl()
        self.assertFalse(report["W04"]["agent_ready"])
        self.assertEqual(
            report["W04"]["unresolved"],
            [{"id": "W04", "executor": "tbd"}, {"id": "E04", "executor": "tbd"}],
        )
        self.assertEqual(report["W01"]["executor"], "unknown")
        self.assertEqual(report["W01"]["epics"], {"E04": "unknown"})
        self.assertTrue(report["W01"]["agent_ready"])

    def test_a_human_task_after_unfinished_agent_work_of_its_wave_fails(self):
        head = wave(executor="human", epic="human")
        agent = task("E04-T01", touches=["a"], executor="agent")
        middle = task(
            "E04-T02", ["E04-T01"], touches=["b"], executor="human", state="done"
        )
        late = task("E04-T03", ["E04-T02"], touches=["c"], executor="human")
        errors = self.fails(agent, middle, late, head=head)
        self.assertIn("E04-T03 is a human task that waits", errors)
        self.assertIn("['E04-T01']", errors)
        finished = agent.replace("State: todo", "State: done")
        self.passes(finished, middle, late, head=head)

    def test_a_human_task_after_a_qa_task_of_its_wave_fails(self):
        errors = self.fails(
            task("E04-T01", touches=["a"], executor="agent"),
            qa("E04-QA1", ["E04-T01"]),
            task("E04-T02", ["E04-QA1"], touches=["b"], executor="human"),
            head=wave(executor="human", epic="human"),
        )
        self.assertIn("['E04-QA1', 'E04-T01']", errors)

    def test_the_wave_and_its_epics_agree_with_their_tasks(self):
        human = task("E04-T01", executor="human")
        epic = self.fails(human, head=wave(executor="human", epic="agent"))
        self.assertIn("E04 declares `agent` but has the human tasks", epic)
        whole = self.fails(human, head=wave(executor="agent", epic="human"))
        self.assertIn("the wave declares `agent` but has the human tasks", whole)
        self.assertIn("the human epics ['E04']", whole)
        empty = self.fails(
            task("E04-T01", executor="agent"), head=wave(executor="human", epic="human")
        )
        self.assertIn("declares `human` but has no human task", empty)
        self.passes(human, head=wave(executor="human", epic="human"))

    def test_a_brief_never_says_tbd_and_version_3_needs_each_executor(self):
        self.assertIn(
            "has `Executor: tbd`",
            self.fails(task("E04-T01", executor="tbd"), head=wave()),
        )
        missing = self.fails(task("E04-T01"), head=wave(executor=None, epic=None))
        self.assertIn("the front matter has no `executor`", missing)
        self.assertIn("E04 has no `- Executor:` line", missing)
        self.assertIn("E04-T01 has no `Executor`", missing)

    def test_a_legacy_file_without_executor_lines_passes(self):
        legacy = wave(executor=None, epic=None, version="2.0.0")
        self.passes(task("E04-T01"), task("E04-T02", ["E04-T01"]), head=legacy)
        self.assertIn(
            "has `Executor: tbd`",
            self.fails(task("E04-T01", executor="tbd"), head=legacy),
        )

    def test_hitl_fails_on_an_executor_that_the_graph_check_rejects(self):
        (self.waves / "W02-x.md").write_text(wave() + task("E04-T01", executor="humna"))
        (self.waves / "W03-y.md").write_text(
            wave(executor=None, epic=None, status="planned").replace("W02", "W03")
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--hitl", str(self.waves)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        errors = " ".join(json.loads(result.stderr.splitlines()[-1])["errors"])
        self.assertIn("E04-T01 has `Executor: humna`", errors)
        self.assertIn("W03-y.md:1: the front matter has no `executor`", errors)
        self.assertIn("E04 has no `- Executor:` line", errors)

    def test_hitl_fails_on_an_active_wave_that_disagrees_with_its_tasks(self):
        (self.waves / "W02-x.md").write_text(
            wave(executor="human") + task("E04-T01", executor="agent")
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--hitl", str(self.waves)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("the wave declares `human`", result.stderr)

    def test_hitl_needs_a_folder(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--hitl", str(self.waves / "none.md")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
