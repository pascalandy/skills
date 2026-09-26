<!-- Moved verbatim from the plan, https://github.com/pascalandy/skills/issues/23. Change the contract there first. -->

## CLI contract: `jevgate`

This section and the next move verbatim into the skill's `references/cli-contract.md` and `references/gate-catalog.md` at U3.

```text
jevgate doctor [--online]
jevgate gates [--check]
jevgate run <gate> [--base REF] [--pr N]
                   [--run-ci | --ci-status pass|fail --ci-sha SHA]
                   [--dry-run] [--no-cache] [--model ID] [--max-requests N]
jevgate explain [<run-id>|last] [--all]
jevgate replay <run-id> [--policy FILE]
jevgate label <run-id>|last --scope gate|question:<id>[@<item>] --outcome good|bad|unknown
              --by human|model|reproduced --evidence TEXT|FILE [--admit]
jevgate version
jevgate help [<command>|<gate>]
```

Every command accepts `--json`, `-h`, `-q`, `-v`, and `--no-color`. `NO_COLOR` is honored. Help wins over other flags; otherwise `--json` wins over `-q`. JSON commands emit one object on stdout, with diagnostics on stderr.

| Command | Does | Network |
| --- | --- | --- |
| `doctor` | Checks the runtime, config, collectors, key source, permission and terms, and engine version, hash, and local-edit status. `--online` adds `GET /v1/models` and reports when `jev-latest` no longer matches the pin | Only with `--online` |
| `gates` | Lists gates, questions, and bands. `--check` enforces the mechanical checklist items: every backticked path exists in collector state, every Choice has a no-match option, every Score has 2–10 levels, every question declares a direction and two thresholds | None |
| `run` | Collects, sanitizes, asks, decides, and records | Yes, unless `--dry-run` |
| `explain` | Prints a run's summary and writes the full state, requests, and answers to a file it names. `--all` prints everything | None |
| `replay` | Recomputes a saved run's verdict from its stored answers. `--policy` applies a band-override file | None |
| `label` | Records an outcome beside a run. `--admit` re-checks privacy and copies the run into `.jev/cases/<id>/` with `labels.toml` | None |
| `version` | Prints the engine version, source hash, and local-edit status | None |

### Help

- `jevgate` with no arguments prints the top-level help and exits 0
- `-h` and `--help` work on every command and ignore every other argument
- `jevgate run <gate> --help` shows the gate's purpose, its questions and bands, its flags, and two examples. The gate file supplies this text, so project gates document themselves
- Help runs no check command, reads no key, makes no network call, and writes nothing. Bootstrap uv and locked dependencies before testing offline operation. Missing or invalid project config falls back to generic help with a diagnostic
- The recipes forward their arguments, so `just jev-merge --help` prints the same text as `jevgate run merge --help`

### `run` flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `--base REF` | Config `integration_ref` | Judge the commit range `base..HEAD` |
| `--pr N` | Detected through `gh` when available | Take claims from the PR title and body; otherwise claims come from commit messages in the range |
| `--run-ci` | Off in `jevgate`, on in `just jev-merge` | Run the configured check command and record `{sha, command, exit, duration}`. A later run on the same clean SHA reuses that record |
| `--ci-status pass\|fail` with `--ci-sha SHA` | None | For a check that already ran elsewhere. A SHA mismatch or a dirty tree gives `insufficient` |
| `--dry-run` | Off | Print the planned groups, claims, bytes, estimated tokens, and cost, and write the full request bodies to a file it names. No network, no check run, no record. Takes precedence over `--run-ci` |
| `--no-cache` | Off | Skip cache reads |
| `--model ID` | Config pin | One-off versioned model override, recorded in the run and used in the cache key. Aliases are not accepted as pins |
| `--max-requests N` | Config value | Positive logical-request cap, including the author request and cache hits. Groups beyond it stay unjudged |

Without `--run-ci` or `--ci-status`, the check result is unknown and the verdict is `insufficient`.

### Revision and request contract

- Resolve base and HEAD once. Record both tips, the merge base, and the judged `base..HEAD` commit list. Collect the branch patch from merge base to HEAD; detect conflicts against the resolved base without changing the working tree. Missing refs or history give `insufficient` with a fetch instruction, never an automatic fetch
- Check cleanliness before and after checks, before sending, and before publishing a verdict. Include staged, unstaged, and nonignored untracked changes. A changed HEAD or dirty tree invalidates the evidence. Reuse a check only for the same repository, clean SHA, and configured command. Imported results record their external provenance
- Offline commands, including dry-run, never invoke networked `gh`. Use locally saved PR text when available, otherwise commit messages, and report the source. A live PR lookup records repository, PR number, and text digest. Never silently treat a failed explicit `--pr` lookup as a successful lookup
- Expand all question instances and paired citations before budgeting. Use stable ordering and unique question/scope/item identities. Reserve the author-text request first, then groups in sorted order. Cache contents do not change coverage
- Check both limits: configured state plus longest question at 30,000 estimated tokens, and state plus all questions below 64,000. Include criteria and citations. A Choice permits at most 254 hunk IDs plus `none`. If a group or author request cannot fit, mark it unjudged and escalate. Never silently truncate evidence or split the settled one-request-per-group design
- Sanitize and scan the entire outbound plan before the first request, including author text and selected existing tests. Dry-run uses the same planner and writes only sanitized payload exports under an ignored directory. Apply deny rules to old and new rename paths. A secret hit writes a redacted diagnostic, never the secret or unsafe payload

### Verdicts, next moves, and exit codes

Each verdict names one kind of next move:

| Verdict | Exit | Means | Next move |
| --- | --- | --- | --- |
| `pass` | 0 | Every applicable decision condition is satisfied after aggregation. It is not authorization to merge or deploy | Continue |
| `escalate` | 10 | Jev could not or should not judge alone: an uncertain or adverse answer, a group left unjudged by size, deny glob, or request cap, or a flagged risk with no pack | `review`: a person or a named reasoning review |
| `block` | 11 | A known deterministic failure: a red check, a conflict, or a secret-scan hit in what would be sent. Jev is not called and nothing is sent | `fix` |
| `insufficient` | 12 | Evidence the agent can obtain: an unknown or stale check result, a dirty tree, or a pack's required proof | `gather` |

Other exits: 1 for engine errors, with `error.kind` set to `config`, `credentials`, `permission`, `service`, or `internal`. 2 for usage errors, and 130 when interrupted. Failures print `error: <what went wrong and how to fix it>` on stderr, then `rerun with --verbose for details`.

### Transport and error behavior

Use the SDK's bounded retry policy once, without an outer retry loop: two retries, a 30-second total retry budget, and 10-second HTTP-operation timeouts. Honor retry headers within that budget. Report exhausted retries as `service`; never retry 401 or 422 blindly. Retries do not expand the planned group coverage.

Validate complete response IDs, primitive shapes, finite probabilities, citation membership, and the answering model before caching or deciding. Missing, malformed, or mismatched responses are `service` errors, never favorable defaults. Preserve completed responses after a partial failure in an error record with no verdict. JSON errors contain `error.kind`, a remediation, and a record path when one could be written. Help and dry-run do not resolve credentials. Operational errors remain errors even when earlier requests succeeded.

### Output

Human output leads with three progress lines on stderr (check, evidence, Jev). Stdout then lists every question asked, grouped by file group. Each line shows the answer, its probability, its band, and the band's threshold. The verdict follows, with numbered reasons, cited hunks, and next moves. `-q` prints the verdict line only.

```text
host  (host.py, host_route.py, tailscale.py, test_host.py)
  claim "apply one owned Serve route" supported   yes 0.93   favorable >= 0.80
  new behavior tested                             yes 0.88   favorable >= 0.80
  an existing test got weaker                     yes 0.04   favorable <= 0.20
  rule contract-first violated                    yes 0.09   favorable <= 0.20
  risk: deploy-config                             yes 0.97   flagged >= 0.50   no pack yet
guides
  rule examples-match-cli violated                yes 0.46   uncertain 0.20-0.80

verdict: escalate (advisory), 2 reasons
  1. risk deploy-config 0.97, host_route.py@@88, cite confidence 0.81 -> review
  2. rule examples-match-cli 0.46, guides/core.md@@41 -> review
next: review host_route.py@@88; compare guides/core.md with `html-publish host --help`
```

The example uses Pilot 1's real PR #62 groups with invented values.

`run --json` prints exactly one object on stdout (`schema: jevgate.run/v1`) with the same numbers. This abbreviated output example omits stored policy and payload fields:

```json
{
  "schema": "jevgate.run/v1",
  "run_id": "20260926T204512Z-merge-8dde",
  "gate": "merge",
  "verdict": "escalate",
  "advisory": true,
  "engine": { "version": "0.1.0", "hash": "sha256:3c1f…", "modified": false },
  "model": { "requested": "jev-1.13.0", "answered": "jev-1.13.0" },
  "judged": { "base": "a17c9b2", "head": "8dde85a", "commits": [{ "sha": "8dde85a", "patch_id": "5e0b…" }] },
  "check": { "sha": "8dde85a", "command": "just check", "exit": 0, "duration_s": 41.2, "reused": false },
  "usage": { "requests": 6, "input_tokens": 23810, "cost_usd": 0.001, "latency_ms": 612, "cached": 0 },
  "evidence": { "groups": 9, "claims": 5, "omitted": [{ "path": "uv.lock", "why": "lock file" }] },
  "answers": [
    { "question": "risk_deploy_config", "primitive": "noul", "scope": "group:host", "value": 0.97,
      "band": { "direction": "yes_is_bad", "favorable": 0.5, "adverse": 0.5 }, "result": "adverse" }
  ],
  "reasons": [
    { "kind": "risk_without_pack", "scope": "group:host", "question": "risk_deploy_config", "value": 0.97,
      "band": "adverse", "cited_hunk": "html_publish/host_route.py@@88", "cite_confidence": 0.81, "route": "review" }
  ],
  "next": [{ "action": "review", "route": "human", "target": "html_publish/host_route.py@@88" }],
  "record": ".jev/runs/20260926T204512Z-merge-8dde.json"
}
```

### Credentials, configuration, and permission

- **Key.** `TYPESAFE_API_KEY` first, then `chezmoi secret keyring get --service=typesafe_ai --user=api_key` with a 15-second timeout. Without chezmoi the fallback is skipped. Never from a flag. `doctor` reports which source worked, never the value; on keyring exit 36 it explains the locked macOS keychain and says to set the variable.
- **Precedence.** Flags, then `JEVGATE_*` environment variables, then `.jev/config.toml`, then built-in defaults. Permission and terms come only from the reviewed `[privacy]` table; generic overrides cannot grant consent or shrink the base deny list.
- **Permission.** `.jev/config.toml` holds a `[privacy]` table: `send_code`, `commit_cases`, `approved_by`, `approved_on`, and `terms`. `send_code` covers diff hunks, claims from PR text or commit messages, and check facts, including re-asked cases later. `terms` names the approved summary of TypeSafe's terms (US hosting, derived telemetry allowed, no fixed retention, zero retention for enterprise only). The engine carries the current summary's name.
  - Until `send_code = true` and the terms name matches, live runs exit 1 with `error.kind = "permission"`. `--dry-run`, `explain`, `replay`, and `label` keep working.
  - With `commit_cases = false`, setup adds `.jev/cases/` to `.gitignore`, and everything works on that machine only.
  - No repository gets a default, public or private: setup shows a `--dry-run` payload and obtains both answers. Existing explicit approval remains valid within its recorded scope and terms; do not ask again merely because setup is rerun. The gate runs before push, so it can send commits nobody has published yet.
- **Sanitization.** Permission never relaxes any of these:
  - a base deny list that projects can extend and never shrink: `.env`, `.env.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`, `id_ed25519*`, `*.age`, `*.gpg`, `*.kdbx`, `**/secrets/**`
  - project deny globs from config
  - any path the project's git ignore rules match, even when tracked
  - the secret scan: the project's gitleaks when present, built-in patterns otherwise. A hit blocks and sends nothing

  Deny globs and ignore rules only omit and list; a group that loses files this way stays unjudged and escalates.

### Engine distribution

- `.jev/jevgate.py` is one PEP 723 file run with `uv run --script`. Its header pins `typesafe-sdk` exactly and sets `requires-python = ">=3.11"` for `tomllib`. `uv lock --script` writes `.jev/jevgate.py.lock` beside it.
- The header stamps the engine version and a source hash that covers the file without its stamp lines.
- Local edits are allowed and visible: `doctor` reports the hash mismatch, and every run record carries `engine.modified: true` and the hash.
- Rerunning the create skill upgrades the engine. It compares the project's engine version with its canonical copy, shows the diff before replacing an edited engine, and keeps config, packs, cases, and runs.
- The engine reads every record schema it has ever written. Admitted cases are never rewritten.
- The engine bootstraps through `uv`; live inference needs the key. Project proof also needs Git, just, and the project's check dependencies. Offline guarantees apply after runtime and dependency bootstrap.

### Records, labels, and cases

- **One record schema.** A run record (`jevgate.run/v1`) holds sanitized state, exact requests, responses, verdict or error, reasons, effective gate and pack definitions plus their hashes, applicability and aggregation bindings, model requested and answered, judged commits with SHAs and patch-ids, check facts, omissions, and usage. Records live in ignored `.jev/runs/`. Hashes alone are insufficient for replay
- **Replay.** Read the saved policy and evidence, never today's packs or working tree. `--policy` accepts band overrides only and leaves the original record unchanged. Reject changes to questions, applicability, collectors, or model. Resolve IDs in runs and admitted cases through one reader
- **Exact cache.** Hash the canonical outbound body and effective versioned model, including overrides. Cache only complete validated responses. Keep SHAs, timestamps, run IDs, and check facts out of outbound state; the record binds answers to the revision. Permission may cover more than the actual payload. The ignored `.jev/cache/` stores answers, not verdicts. Reapply current bands after lookup. Cache hits preserve original usage separately and charge zero new inference tokens or cost. `--no-cache` skips reads but still writes validated responses
- **Durability.** Write records, cache entries, and admitted cases atomically. Use unique run IDs, resolve `last` once, and expose only completed writes. Prefer explicit run IDs in multi-command workflows. Repeated admission preserves immutable case bytes and label history. Persistence failure exits 1 with `internal`; it cannot print a successful verdict
- **Labels.** After an escalation is resolved, or when a passed change later proves wrong, `just jev label last` records the outcome beside the run:
  - `--scope` names the gate or one question and item
  - `--outcome` is `good`, `bad`, or `unknown`. At gate scope it assesses the captured change against the gate requirements. At question scope it assesses the condition in that question's favorable or adverse direction. It never labels whether Jev agreed with the reviewer. No later fix means unknown, never good; a later fix does not turn the original revision good
  - `--by` names the provenance: `human`, `model`, or `reproduced`
  - `--evidence` holds the review
- **Admission.** `label --admit` re-runs the privacy checks and copies the run into `.jev/cases/<id>/` with `labels.toml`. The project skill admits every run where the gate was wrong, in either direction. Admission refuses a run whose inputs are missing or fail the privacy checks. Superseding a label keeps its earlier value and reason.
- An admitted case replays in a fresh clone without runs, cache, network, or key, because a case is a run record.
