---
name: Release
description: Steps to publish a tagged release
tags:
  - area/ea
  - kind/doc
  - topic/playbook
  - status/stable
date_created: 2026-09-26
date_updated: 2026-10-04
---

A pushed `vX.Y.Z` tag publishes nothing by itself. From `main` on your machine, validate the tag and publish a GitHub Release with that version's `CHANGELOG.md` notes

## Steps

1. Choose `vX.Y.Z` using the 0.x policy in `CHANGELOG.md`
2. Run `just release-check vX.Y.Z --verbose` to list changed skills
3. Write that version's `CHANGELOG.md` section and merge it to `main`
4. On `main`, run `just check --sweep && just release-check vX.Y.Z`; when HEAD is ready, the first answers `{"ok":true}` and the second prints nothing
5. Run `git tag vX.Y.Z && git push origin vX.Y.Z`
6. Publish from the same HEAD: `notes=$(mktemp) && just release-check vX.Y.Z --notes "$notes" && gh release create vX.Y.Z --verify-tag --title vX.Y.Z --notes-file "$notes"`
7. Never move or delete a pushed tag, or edit or replace a published release
8. If step 6 fails, rerun it once only when the failure was transient; otherwise fix on `main` and release the next patch

## Related

- [[checks]]
- [[script-conventions]]
