# Destination collisions

The archive command preserves an occupied destination and publishes the new
archive at the next numbered name.

## Sub-features

- `collision.existing-preserved` checks the occupied file hash
- `collision.suffixed` checks the selected `(2)` destination
- `collision.archive.*.reopened` checks the published archive
- `collision.source-removed` checks successful cleanup

## How to get to it (user POV)

Run `just convert-video` when the normal archive filename already exists. The
verifier seeds a generated file at that destination.

## Driving it with verify-video-archive

Run this after Launch and Doctor.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature collision
```

Compare the retained before and after archive inventories.

## Gotchas

- The preexisting file is not an operation created by this run
- The expected new destination is exactly `collision (2).mp4`
- Both files must remain readable and the occupied file hash must not change
