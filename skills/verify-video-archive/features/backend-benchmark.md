# Backend benchmark

The benchmark compares software x265 with the hardware HEVC backends that can
run on the target machine. It uses generated media and the real
`just convert-video` archive path.

## Sub-features

- The corpus lock records each generated source hash and media facts
- Each usable backend gets one warm-up and three measured runs per clip
- Each run records full-command and stage timings, candidate bytes before
  fallback, archive bytes, preservation checks, and available resource data
- Resource summaries use maximum observed descendant-tree RSS and CPU across
  repeated runs rather than median or whole-pipeline ratios
- The report applies the per-clip size gate and the 10 percent full-pipeline
  time gate
- Native-scale stills and motion pairs keep the visual gate unmet and store the
  random key separately

## How to get to it (user POV)

Prepare the corpus once. Copy the complete corpus directory when two machines
must use identical source bytes.

## Driving it with verify-video-archive

```sh
just benchmark-video-archive prepare --output ./benchmark-corpus
just benchmark-video-archive run \
  --checkout "$PWD" \
  --corpus ./benchmark-corpus/corpus-lock.json \
  --output ./benchmark-evidence
just benchmark-video-archive evidence \
  --manifest ./benchmark-evidence/manifest.json
```

## Gotchas

- Encoder-name presence is inventory data. Only a successful archive run makes
  a backend usable for that clip
- Benchmark backend trials are strict and never retry with software x265, so a
  retained hardware failure cannot be reported as hardware success
- An approved production hardware selection must retry a missing device,
  unsupported input, or encoder runtime failure once with software x265 and
  report the reason; no hardware backend is currently approved
- Read the blinded artifacts before the separate key
- Evidence from one physical machine approves no other machine
- Keep software x265 when any size, preservation, speed, or visual gate fails
