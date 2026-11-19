# QA task

Read this file when you are the QA agent and you do a QA task.
If the PM starts you only to check `qa-recheck` findings again, do step 1, then step 13.

1. Confirm that this session runs on the QA machine that `01-project.md` names. If it does not, stop and tell the PM
2. Take a ready issue with the label `qa`: each of its blockers is closed and it has no assignee
   - If this session wrote or reviewed code for a task that the issue tests, stop and tell the planner
3. Assign the issue to yourself
4. Read the QA brief, the briefs of the tasks that it tests, the linked sections of the business case and the agent file
   - Run each `check` of the `needs` in the QA brief. If one fails, stop, comment the command and its output on the issue, and add the label `0-impediment`
5. Start the system as the agent file says
6. Before you read a diff or a PR discussion, do each QA scenario on the default branch
7. Run each acceptance item of each tested task, and the `Verify` command, on the default branch
8. Examine the edge cases near the scenarios
9. Open one issue for each finding, as [Findings and verdicts](../SKILL.md#findings-and-verdicts) says
10. Post the QA report on the QA issue. The report contains:
    - A summary of 3 lines for the PM, who uses it to decide the UAT
    - The scenarios that you ran
    - The evidence: commands with their output, and screenshots
    - The findings
    - The verdict
    - The line `Independence: fresh session on <QA machine>, no implementation context; verified PRs #57 #58`
11. Set the verdict label: `qa:accepted`, `qa:accepted-with-findings` or `qa:rejected`
12. If [the graph script](../SKILL.md#graph-script) lists this QA task in `gates` and the verdict is `rejected`, keep the QA issue open. In all other cases, close it
13. For each open `qa-finding` issue whose fix task is closed, or that has the label `qa-recheck`, run its reproduction on the default branch and comment the evidence
    - Remove the label `qa-recheck`
    - If the reproduction passes, close the finding
    - If the reproduction fails and the finding has a fix task, open the fix task again
