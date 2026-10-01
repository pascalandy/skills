# Stack routing acceptance cases

| Case | Expected behavior |
| --- | --- |
| One issue is requested | Do not infer a stack from the issue count alone |
| Several dependent review units tell one coherent story | Evaluate `gh-stack` before implementation |
| Several units are independent, merely concurrent, or share only ancestry | Use ordinary PRs |
| A selected playbook owns stack topology or landing | Follow that playbook and load `gh-stack` only when it delegates there |
