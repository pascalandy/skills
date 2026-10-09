# Learnings

Read to understand why a rule in this skill exists, or when writing a learning at the end of a project. The rules themselves live in the references, the playbooks and `scripts/check_page.py`.

## Write a learning

Write one at the end of a Livrable, or when a QA loop found something the references did not cover.

1. Name the file `YYYY-MM-DD-<use-case>.md`, with the project's last day. Describe the use case, never the client: no client name, product name, private URL or quoted text, since this repository is public
2. Write four sections: the use case, what it took (rounds, findings, time), the root causes, and where each lesson went
3. Move each lesson into its home before you finish: a row in `references/pitfalls.md`, an item in `references/quality-bar.md`, a check in `scripts/check_page.py`, or a step in a playbook. A lesson that stays only in its learning is lost to the next agent
4. Add the learning to the index below

Done when every lesson names its home and that home holds it.

## Index

| Date | Use case | File |
| --- | --- | --- |
| 2026-10-09 | A guided reading page built from a client's PDF | `2026-10-09-page-de-lecture-guidee-depuis-un-pdf.md` |
