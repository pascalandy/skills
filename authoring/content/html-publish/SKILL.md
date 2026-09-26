---
name: "html-publish"
description: "Use when publishing, updating, inspecting, or recovering a standalone HTML artifact through the configured html-publish service with a durable receipt. Use html-mode for artifact design and browser review."
---

# HTML publish

Delegate publication to the installed `html-publish` executable. Its `artifact` group owns the durable receipt: publication name, target, accepted revision, immutable pending bytes, and retry identity. The publisher decides archive, activation, conflict, and delivery outcomes.

## Prerequisite

An installed `html-publish` wheel whose `artifact` and `skills` groups answer. Check both groups before the first command:

```sh
html-publish skills list
html-publish artifact --help
```

If either check fails, install or update the reviewed wheel first; the package README and its operations guide own those commands. Package installation and this skill's rollout stay separate coordinated steps; never assume a host has both.

## Publish

The client configuration defaults to `~/.config/html-publish/client.json`. Omit `--config` to use it. Add `--config PATH` before the subcommand only when selecting another file.

Create the first publication with an explicit stable name:

```sh
html-publish artifact publish SOURCE --new NAME
```

For later edits, use the same artifact and sibling receipt:

```sh
html-publish artifact publish SOURCE
```

A normal publish makes one publisher call. Do not add plan, status, history, or verify calls unless the result requires diagnosis. An explicit local-only request wins. It neither invokes the publisher nor changes a receipt:

```sh
html-publish artifact publish SOURCE --local-only
```

## Recover

If a publish result is uncertain or delivery failed, retry the frozen attempt. If the publish
command used `--config PATH`, add the same option to retry; the receipt does not remember a custom
configuration path. The retry keeps the saved bytes, attempt ID, target, and original
expectation, and never substitutes a current source file for a pending snapshot:

```sh
html-publish artifact retry --receipt BUNDLE
```

Read the saved receipt state without invoking a host. This records nothing:

```sh
html-publish artifact status --receipt BUNDLE --local-only
```

With the selected configuration and without `--local-only`, status records an observation. An
observation never changes the accepted revision:

```sh
html-publish artifact status --receipt BUNDLE
```

For any non-success result, run `html-publish skills get recovery` and follow it. That guide owns error codes, conflict replacement with `--reviewed-revision` and `--replaces-attempt`, lost-receipt adoption with `--adopt`, and the version 2 upgrade after a first restore. Adoption keeps the accepted baseline null until a correlated publish result qualifies. Read `html-publish skills get core` for the full publish, update, and restore patterns.

## Handoff

Return the tool's JSON. Keep browser review, host delivery verification, a separate client probe, and receipt persistence as distinct facts. Report a private URL only when a verified result carries one. If publication cannot complete, keep the local artifact and the retained receipt, then report the exact retry command without creating another publication identity. Production publication remains gated by html-publish issue 6 recording the approved reboot and installed proof.
