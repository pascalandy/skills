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

    def run_on(self, *briefs, name="W02-x.md"):
        path = self.waves / name
        path.write_text("# W02\n\n### E04: epic\n\n" + "\n".join(briefs))
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            capture_output=True,
            text=True,
            check=False,
        )

    def passes(self, *briefs):
        result = self.run_on(*briefs)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

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

    def test_a_qa_task_that_no_task_names_gates_nothing(self):
        answer = self.passes(task("E04-T01"), qa("E04-QA1", ["E04-T01"]))
        self.assertEqual(answer["gates"], {})

    def test_parallel_tasks_with_a_common_path_fail(self):
        errors = self.fails(
            task("E04-T01", touches=["src/auth/**"]),
            task("E04-T02", touches=["src/auth/db.ts"]),
        )
        self.assertIn("E04-T01 and E04-T02 can run at the same time", errors)

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
