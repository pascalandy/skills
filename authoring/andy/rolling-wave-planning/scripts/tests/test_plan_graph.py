"""Run plan_graph.py on wave files written in a temporary plan folder."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "plan_graph.py"


def task(brief_id, blocked_by=(), touches=("src/a.ts",), state="todo", needs=()):
    block = {
        "id": brief_id,
        "blocked_by": [{"id": blocker, "why": "contract"} for blocker in blocked_by],
        "needs": list(needs),
        "touches": list(touches),
    }
    return brief(brief_id, block, f"- Kind: feature · State: {state}")


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

    def run_on(self, *briefs, name="W02-x.md", flags=()):
        path = self.waves / name
        path.write_text("# W02\n\n### E04: epic\n\n" + "\n".join(briefs))
        return subprocess.run(
            [sys.executable, str(SCRIPT), *flags, str(path)],
            capture_output=True,
            text=True,
            check=False,
        )

    def passes(self, *briefs):
        result = self.run_on(*briefs)
        self.assertEqual(result.returncode, 0, result.stderr)
        answer = json.loads(result.stdout)
        self.assertEqual(answer["file"], str(self.waves / "W02-x.graph.json"))
        return json.loads(Path(answer["file"]).read_text())

    def fails(self, *briefs):
        result = self.run_on(*briefs)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(result.stdout, "")
        answer = json.loads(result.stderr.splitlines()[-1])
        self.assertFalse(answer["ok"])
        return " ".join(answer["errors"])

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


if __name__ == "__main__":
    unittest.main()
