# Parallel batch

## Sub-features

- 100 real generated videos with exact result, outcome, operation, source, and archive counts
- Serial, normal, and maximum resource measurements
- Six 1280x720 videos for a representative maximum-mode resource measurement
- Selected and observed worker bounds
- File-local work isolated from coordinator publication
- Real second-invocation lock contention with exit 75
- SIGINT exit 130 within ten seconds with no owned media process left behind
- Recovery without duplicate publication

## How to get to it (user POV)

Run `just convert-video` against a large input folder. The default normal mode
keeps CPU and memory reserves for other applications. Use
`--resource-mode maximum` for the measured safe capacity, or `--jobs N` to set
a lower cap.

Press Ctrl+C once to stop new scheduling and terminate media work owned by the
current invocation. Run the same command again to reconcile durable work and
finish the retained sources.

## Driving it with verify-video-archive

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  run --checkout "$CHECKOUT" --feature parallel-batch
```

Run this command on both target machines. Retain each printed manifest path.
Run Evidence again after moving the bundle to prove that every referenced file
and SHA-256 remains valid.

## Gotchas

- A copied generated fixture is still decoded and encoded as real media for every source
- The 100-video fixtures prove accounting and lifecycle behavior; the separate 1280x720 workload proves the resource bound under representative load
- The observed process bound counts FFmpeg and FFprobe processes, not Python worker threads
- Software x265 has no hardware encoder-session limit, so the evidence records that metric as not applicable
- A target-platform result proves only the named machine
- The verifier never reads personal media or the default real home
