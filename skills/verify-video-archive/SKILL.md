---
name: "verify-video-archive"
description: "Use when validating the macOS or Linux archive workflow reached by `just convert-video`, including real media, prerequisites, terminal progress, source safety, locking, and recovery."
---

# Verify video archive

Drive the checkout implementation through `just convert-video`. The verifier
creates generated media and never reads the real archive or personal input
folders.

Load this skill from
`dot_config/ai_templates/skills/verify/verify-video-archive/SKILL.md` in a
dotfiles checkout. After skill synchronization, you can invoke
`$verify-video-archive` and resolve `VERIFY_DIR` from the loaded skill directory.

## Launch

Create a new run. The command prints the retained manifest path.

```bash
VERIFY_DIR="<verify-video-archive-skill-dir>"
CHECKOUT="<dotfiles-checkout>"
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  launch --checkout "$CHECKOUT"
```

Copy the printed `manifest` value into `MANIFEST`. Launch creates a unique
disposable root and a separate evidence root. Each scenario gets its own home,
input roots, archive, state, journal, and scratch directories.

## Doctor

Run Doctor before Drive.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  doctor --manifest "$MANIFEST"
```

Doctor checks macOS or Linux, Python 3.11 or newer, Just, Git, FFmpeg, FFprobe,
`libx265`, a resolved `lsof` executable, and the checkout wrapper. An unmet
check blocks real-media acceptance on that platform.

## Drive

Read [the feature map](features/README.md), then run one feature or the full map.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature conversion

uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature all
```

Every archive invocation executes this argument array:

```text
<resolved-just> --justfile <checkout>/justfile convert-video
```

The isolated `~/.local/bin/video-archive` is a symbolic link to the checkout
wrapper. It adds no archive behavior. The Just recipe supplies the real
`archive` subcommand and uses the isolated default folders.

The recovery feature sets the verifier-only
`VIDEO_ARCHIVE_VERIFY_PAUSE_AFTER_PREPARED_SECONDS` environment variable. The
archive command pauses only after its durable `prepared` record. The verifier
stops and kills the process group created for that invocation, then runs the
same Just command again without the pause.

Progress scenarios run the real Just command in a task-owned PTY. The driver
sets the PTY width with the terminal interface for the narrow-layout check. It
does not fake outcome data. Generated media, archive state, exit status, and
retained transcripts prove each outcome.

The dependency feature runs the real Just recipe with task-owned restricted
`PATH` directories. It proves that missing Python, FFmpeg, FFprobe, `libx265`,
or `lsof` fails before the source or archive changes.

The parallel-batch feature creates 100 generated videos for each serial,
normal, maximum, and cancellation run. It records selected limits, observed
simultaneous media processes, throughput, elapsed time, peak RSS, CPU use, and
backend-session applicability. During the cancellation run, it starts a second
real archive invocation and requires exit 75 before it sends one SIGINT to the
first invocation. It then verifies exit 130, owned-child cleanup, recovery, and
exact final accounting. A separate six-video 1280x720 workload exercises the
maximum-mode worker bound with representative media instead of relying on the
small 100-video correctness fixtures for resource safety.

## Evidence

Validate the retained bundle after Drive.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  evidence --manifest "$MANIFEST"
```

Read `manifest.json` first. It records exact argument arrays, exit status,
transcripts, Git revision and dirty identity, platform and tool versions,
inventories, hashes, FFprobe output, operation records, and check status.
`skipped` and `unmet` remain separate from `passed`.

For a target-platform acceptance run, use `--feature parallel-batch` and retain
the complete bundle. Run the feature on both Linux and Apple M2 hardware. A run
from another machine does not satisfy either target gate.

Evidence paths are relative to `manifest.json`. You can move the complete
bundle and run Evidence again. It rechecks every retained path and SHA-256.

The verifier independently reopens each successful archive with FFprobe,
decodes it with FFmpeg, and compares its hash with the durable operation record.
The production store remains responsible for verifying publication before it
removes a source.

See [the evidence schema](references/evidence-schema.md) when reviewing or
extending the manifest.

## Cleanup

Remove only the disposable root named by the manifest.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  cleanup --manifest "$MANIFEST"
```

Cleanup checks the run ID and random owner token before removal. It refuses a
symbolic link, a broad path, a changed marker, or evidence stored below the run
root. Cleanup never loads a PID or signals a process. The evidence bundle and
manifest survive.

## Helpers

Run the whole lifecycle when you do not need to inspect the run before cleanup.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  run --checkout "$CHECKOUT" --feature all
```

## Benchmark backends

For backend performance and compression qualification, read
[the backend benchmark feature](features/backend-benchmark.md). Its command
uses generated media and invokes the same `just convert-video` entry point.
Keep its visual gate unmet until a reviewer finishes the blinded comparison.

Run focused helper tests after changing the verifier.

```bash
uv run --no-project python -m unittest discover \
  -s "$VERIFY_DIR/scripts/tests" -v
```

Run repository checks from the checkout. Each platform acceptance gate is the
first command plus a passing full Drive run on that platform.

```bash
just test-video-archive
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  run --checkout "$CHECKOUT" --feature all
```
