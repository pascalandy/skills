# Skill: Eval Rubric

When evaluating artifact against acceptance criteria, judge one criterion at a time. Only inspect final observable result. Do not reward hidden reasoning, effort, or intent.

## Rating System

| Score | Label | Meaning | Final answer |
| ----- | --------------------- | -------------------------------------------------------------------------------------------------------- | ------------ |
| 4 | Strong pass | Clearly meets criterion with strong observable evidence | yes |
| 3 | Pass | Meets criterion; only minor non-material issues are allowed | yes |
| 2 | Insufficient evidence | Criterion is not clearly met, or final artifact provides partial, ambiguous, or missing evidence | no |
| 1 | Clear fail | Clearly does not meet criterion | no |
| 0 | Not applicable | Criterion cannot be judged from final artifact or does not apply to this context | skip |

## Evaluation Logic

For each criterion:

1. Does this criterion apply to this artifact? If not applicable or cannot be judged → `0` (skip).
2. Does artifact clearly fail this criterion? If yes → `1`.
3. Is evidence partial, ambiguous, or missing? If yes → `2`.
4. Does it meet criterion with only minor non-material issues? → `3`.
5. Does it meet criterion with strong, clean evidence? → `4`.

## Output Format

For each criterion, produce exactly:

- **Score**: `0`-`4`
- **Decision**: `yes`, `no`, or `n/a`
- **Justification**: One sentence citing observable evidence from artifact (or why criterion does not apply)

## Key Design Rules

- Binary decision is real output. Numeric score is structured judgment that feeds that decision
- Important threshold is `2` vs `3`
- `3` = "it passes, stop arguing." `4` = "it passes cleanly and convincingly." Both map to `yes`. This prevents withholding top scores for unimportant reasons and avoids unnecessary retry loops
- `3` should be normal passing score. Do not make `4` mandatory
- `2` is strict fail. Borderline must not sneak through
- `0` means "not applicable" -- criterion is excluded from pass/fail tally entirely. It does not count as failure
- Hard blockers should be metadata on criterion, not part of score itself. If blocker gets `no`, whole artifact fails
- Never average scores across criteria. Decision is per-criterion: count pass/fail, do not blend. Criteria scored `0` are excluded from count
