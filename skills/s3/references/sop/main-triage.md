# main-triage

MAIN runs this SOP each time a REV reports. You have the final say on every finding and on when the reviews end.

1. **Premortem.** While BLAST runs, write your own premortem: assume this stack merged and broke something a week later. Which blind spots explain it? Are we adding debt or code smells? Triage your findings with BLAST's. Done when your premortem lists its findings, or says it found none
2. **Decide.** Accept or reject each finding, with a one-line reason. Done when every finding has a decision and a reason
3. **Relay.** Send each accepted finding with `t3_thread_send` to the thread that owns its layer: DOC<n> for the docs PR, COD<n> for the rest. Wait for its report. Done when each owner reports each finding pushed to its layer, or why it could not be
4. **Next.** A REV runs at most the `max-passes` its role sets in `config.toml`. When the fixes need a fresh look and this REV has passes left, rerun it on the new heads with `t3_thread_send`, carrying each prior finding and your decision. Otherwise settle this REV, and DOC<n> too after the pristine review, then move on to the next step of CU1. A thread whose role sets `retro` stays open until `main-closing`. Done when you reran it, or settled it and noted why the review ended for the report
