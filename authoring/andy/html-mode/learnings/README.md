# Learnings

Read when tracing a rule's origin or recording a learning. Rules live in references, playbooks, and `scripts/check_page.py`.

## Write a learning

Write a learning after a Livrable or when QA finds something the references do not cover.

1. Name the file `YYYY-MM-DD-<use-case>.md` with the project's last day. This repository is public. Describe only the use case, without client names, product names, private URLs, or quoted text
2. Write four sections: use case, what it took (rounds, findings, time), root causes, and where each lesson went
3. Add each lesson to `references/pitfalls.md`, `references/quality-bar.md`, `scripts/check_page.py`, or a playbook step
4. Add the learning to the index below

Finish when each lesson names its home and is recorded there.

## Index

| Date | Use case | File |
| --- | --- | --- |
| 2026-10-09 | A guided reading page built from a client's PDF | `2026-10-09-page-de-lecture-guidee-depuis-un-pdf.md` |
