# Video archive verification evidence

The driver writes one `video-archive.verification/v1` manifest for each run.
The manifest is the retained index for raw command evidence and copied media.

## Run identity

Each run records these fields:

- `run_id`, a random identifier used in every owned directory name
- `started_at` and `finished_at`, UTC timestamps
- `checkout`, the absolute checkout path used by Just
- `git.revision`, the A checkout's Git `HEAD`
- `git.dirty`, the A checkout's porcelain status plus a SHA-256 identity for tracked and untracked changes
- `tested_files`, hashes of the A application files
- `verifier`, the B package path, its Git revision when run from the skills source checkout, and hashes of its own files
- `platform`, Python's platform facts, hostname, CPU model, logical CPU count, and the macOS or Linux version
- `tools`, resolved paths and version output for Python, Just, FFmpeg, FFprobe, Git, `lsof`, and `libx265`
- `paths`, the disposable root and every isolated or retained directory

`paths` names distinct `home`, `input`, `archive`, `state`, `journal`,
`scratch`, and `evidence` directories. The evidence directory is never inside
the disposable root.

## Checks

Every check has an `id`, `status`, `summary`, `expected`, `observed`, and
`evidence` list. `status` is one of these values:

- `passed` for an observed real behavior that met its assertion
- `failed` for a behavior that ran and contradicted its assertion
- `skipped` for a check that the selected feature did not request
- `unmet` for a required platform or tool condition that prevented execution

Only `passed` satisfies an acceptance check. The aggregate verdict is `passed`
only when every selected check passed.

## Invocations

Each generated-media command and Just invocation records:

- The exact `argv` array and working directory
- The explicit environment overrides without inherited environment values
- The start and finish timestamps
- The process ID and process group ID when a live child was owned
- The exit status or terminating signal
- Paths to retained standard output and standard error transcripts

Measured batch invocations also record wall time, approximate CPU-seconds, peak
descendant-tree RSS, peak descendant-tree CPU percent, peak simultaneous media
processes, and hardware-session applicability. Descendant discovery follows
parent PIDs across process sessions. The batch JSON supplies the resource mode,
requested cap, selected worker count, CPU limit, memory limit, reservations,
available resources, and measured per-worker demand with provenance.

PTY invocations also record `pty: true`, `terminal_width`, signals sent by the
driver, and one combined terminal transcript. Redirected and JSON invocations
retain separate standard output and standard error files.

The recovery scenario also records every signal sent to its owned process
group and the durable operation document observed before termination.
The parallel interruption record adds cancellation latency, owned media PIDs
before SIGINT, owned media PIDs after exit, and the second invocation's exit
status.

## Files and media

Inventories contain a relative path, file kind, byte count, and SHA-256 for
each regular file. Media entries also link to raw FFprobe JSON and normalized
facts for the container, codecs, dimensions, frame count, and duration.

The evidence bundle copies the generated sources needed to prove failure
retention and byte-identical fallback. It also copies published archives,
operation records, the journal, and ownership records before cleanup. Every
evidence-file reference is relative to `manifest.json`, so the whole bundle can
move without breaking links. Observed checkout and disposable-run paths remain
absolute facts.

`evidence_files` inventories every retained file except `manifest.json` with a
relative path, byte count, and SHA-256. Running Evidence after relocation
rechecks those paths and hashes.

## Cleanup

The disposable root contains an ownership marker with the run ID and random
token. Cleanup resolves the requested path, rejects symbolic links, checks
the marker, and removes only that exact root. Cleanup does not load a PID from
the manifest or signal a process. The driver reaps every process that it starts
before cleanup begins.

The final manifest records the cleanup result and confirms that the manifest
still exists after cleanup.
