# QA task

Read this file when you are the QA agent and you do a QA task.

You make no commit and no PR.

1. Start a new session on the QA machine that `01-project.md` names
2. Take a ready issue with the label `qa`: each of its blockers is closed and it has no assignee
   - If this session wrote or reviewed code for a task that the issue tests, stop and tell the planner
3. Assign the issue to yourself
4. Read the QA brief, the briefs of the tasks that it tests, the linked sections of the business case and the agent file
5. Start the system as the agent file says
6. Do each QA scenario on the default branch. Read no diff and no PR discussion before this step is complete
7. Run each Acceptance of each tested task on the default branch
8. Examine the edge cases near the scenarios
9. Open one issue for each finding, as [Findings and verdicts](../SKILL.md#findings-and-verdicts) says
10. Post the QA report on the QA issue. The report contains:
    - A summary of 3 lines for the PM, who uses it to decide the UAT
    - The scenarios that you ran
    - The evidence: commands with their output, and screenshots
    - The findings
    - The verdict
    - The line `Independence: fresh session, no implementation context; verified PRs #57 #58`
11. Set the verdict label: `qa:accepted`, `qa:accepted-with-findings` or `qa:rejected`
12. If the brief has `Blocking: yes` and the verdict is `rejected`, keep the QA issue open. In all other cases, close it
13. For each open `qa-finding` issue whose fix task is closed, run its reproduction on the default branch and comment the evidence
    - If the reproduction passes, close the finding
    - If the reproduction fails, open the fix task again
