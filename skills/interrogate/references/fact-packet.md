# Reviewing a fact packet

A fact packet is facts and their artifacts without the author's story, such as a `diagnose` case file with its `artifacts/` folder. The caller names the checkpoint and the reviewer count; `diagnose` asks for one reviewer from another model family. These steps replace Steps 2 to 5 and the output format of `SKILL.md` for a fact packet.

## Step 2, State the question

Name the checkpoint and copy its questions below into the prompt. Give no intent paragraph, no transcript, and no account of why the author believes the leading hypothesis.

| Checkpoint | Questions |
|---|---|
| control | Does each signal differ from the control beyond the noise floor? Is the control broken the same way as the variable? How was each fact gathered: right host, window, build, and tool? Does each absence state its coverage? |
| matrix | How many live hypotheses fit each signal? Does any fact contradict a hypothesis marked `+` or `0`? Were the repair tactics tried before a new hypothesis? Was each descent justified by weak signals? |
| validation | Does one in-scope fact contradict the candidate? Does every claim in the Close or Decisions cite a fact? Remove each member of a combination in turn: which fact goes unexplained? Does the repro show the report's strongest signal? |

## Step 3, Spawn the reviewers

Give each reviewer the case file path, read access to its artifacts and the repository, and this prompt with the checkpoint's questions filled in:

---

You are reviewing an investigation's facts, not its conclusion. Try to eliminate. You may return only these items, each citing fact ids, artifact paths, and lines:

1. A contradicting fact: a hypothesis that fact rules out, as a proposed judgment row `| H# | F# | x | <why the fact rules it out> | reviewer |`
2. A gathering defect: a fact taken from the wrong host, window, build, or tool, or an absence without coverage, as a proposed `reverify` log row
3. A control broken the same way as the variable, with the fact that shows it
4. A missing discriminating fact: one reading that would split the surviving hypotheses, and what each predicts for it
5. A checked null: "I looked for a contradiction in these facts and found none", with the list of facts and artifacts you checked

You can show a hypothesis is wrong; you cannot show one is right, because you cannot see a fact nobody gathered. Never call a hypothesis confirmed, validated, or proven.

Questions for this checkpoint: {CHECKPOINT_QUESTIONS}

Case file: {CASE_FILE_PATH}

---

## Step 4, Synthesize

Check each proposed item against its cited artifact yourself. Drop an item whose citation does not hold, and say why. Merge duplicates. A single reviewer's cited contradiction stands however many reviewers found none.

## Step 5, Verdict

Hand the caller one verdict per live hypothesis and the rows to append. The caller appends each accepted row with `by: reviewer`.

```
### Verdict
- H3: survives F1 to F9, missing: <the discriminating reading, if a reviewer named one>
- H2: eliminated by F5 (<one line on why>)

### Proposed rows
| H2 | F5 | x | <why> | reviewer |
| <step> | reverify | F4 | <the gathering defect> | <what to gather again> |

### Checked
- <reviewer and model family>: <the facts and artifacts it checked>
```

The verdict is "eliminated by F#" or "survives F1 to Fn, missing: ...". It is never "confirmed".
