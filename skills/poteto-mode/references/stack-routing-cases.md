# Stack routing acceptance cases

| Case | Expected behavior |
| --- | --- |
| One issue is requested | Do not infer a stack from the issue count alone |
| Several dependent review units tell one coherent story | Evaluate `gh-stack` before implementation |
| Several units are independent, merely concurrent, or share only ancestry | Use ordinary PRs |
| A selected playbook owns stack topology or landing | Follow that playbook and load `gh-stack` only when it delegates there |
| Build a two-PR stack | Run Feature or Refactoring with `gh-stack` |
| Write the plan of a six-PR migration | Run `playbooks/multi-phase-plan.md` and deliver the plan |
| Write a multi-PR plan, then build its stack | Plan with `playbooks/multi-phase-plan.md`, then implement under Feature or Refactoring with `gh-stack` |
