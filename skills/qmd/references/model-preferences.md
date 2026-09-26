# QMD model preferences

Effective date: [[2026-08-21]]

Use these preferences when recommending, reviewing, or changing QMD model
configuration. They reflect a quality-first setup for an Apple M2 Max with 96 GB
of unified memory and a bilingual French-English vault.

## Preferred models

| Role | QMD key | Preferred model |
|---|---|---|
| Embedding | `models.embed` | `Qwen3-Embedding-0.6B-Q8_0` |
| Query expansion | `models.generate` | `qmd-query-expansion-1.7B-q8_0` |
| Reranking | `models.rerank` | `Qwen3-Reranker-0.6B-Q8_0` |

Use these exact model URIs:

```yaml
models:
  embed: "hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"
  generate: "hf:tobil/qmd-query-expansion-1.7B-gguf/qmd-query-expansion-1.7B-q8_0.gguf"
  rerank: "hf:ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF/qwen3-reranker-0.6b-q8_0.gguf"
```

## Rationale

- Prefer Qwen3 Embedding because the vault is bilingual; QMD documents this
  model family as multilingual across 119 languages
- Prefer the Q8 query-expansion quantization over QMD's Q4_K_M default because
  this machine has ample unified memory and the local preference favors model
  fidelity over saving roughly one gigabyte
- Keep the upstream Q8 reranker because it already matches the quality-first
  preference

The Q8 query-expansion choice is a hardware-backed preference, not a measured
retrieval improvement. Do not claim that it improves recall or answer quality
without a benchmark against the same vault.

## Configuration behavior

Prefer the durable `models:` block in the active `index.yml` over environment
variables. QMD's resolution order is active `index.yml`, environment overrides,
then built-in defaults.

Do not silently substitute a smaller quantization or another model. If a model
cannot load, report the exact failure and ask before changing this preference.

After an approved model change:

1. Run `qmd pull` to fetch the configured models
2. Run `qmd embed` when `models.embed` changed because embeddings from different
   models are incompatible
3. Run `qmd doctor` and `qmd status` to verify the active models and index health

Changing only `models.generate` or `models.rerank` does not require rebuilding
document embeddings. A project-local `.qmd/index.yml` with custom models may
require `qmd trust`; never approve it without the user.
