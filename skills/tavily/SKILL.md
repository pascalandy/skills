---
name: "tavily"
description: "Use when the user explicitly requests Tavily. Never run automatically."
kind: "general"
---

# Tavily REST API

## Overview

Tavily gives LLM-optimized search, content extraction, site mapping, and crawling via REST. Use it only when the user asks for Tavily.

## Routing Policy

| Situation | Tool | Rule |
|---|---|---|
| Explicit user request for Tavily or Exa | Requested tool | Honor the request. |
| Tavily fails to satisfy the request, or the user explicitly asks for corroboration | Exa after Tavily | Sequential escalation is allowed. |
| Local filesystem or repository work | Local tools | Use neither Tavily nor Exa. |

Do not automatically use both tools.

## Quick Reference

| Need | Endpoint | Use Case |
|------|----------|----------|
| Search web | `POST /search` | Find pages, get summaries, optional AI answer |
| Extract from URLs | `POST /extract` | Pull content from specific pages |
| Map site | `POST /map` | Discover all URLs on domain |
| Crawl site | `POST /crawl` | Map + extract in one call |
| Deep research | `POST /research` | Multi-step analysis with citations |

## When to Use

- An explicit user request for Tavily

## When NOT to Use

- Local filesystem or repository work; use local tools
- An explicit user request for Exa
- A search the user did not ask Tavily for
- A request to use both tools at once; escalate to Exa only after Tavily fails or the user asks for corroboration
- API key is missing from keyring (check first)

## Authentication

API key stored in macOS keyring. Retrieve with:

```bash
chezmoi secret keyring get --service=tavily --user=api_key
```

## Base Configuration

```
Base URL: https://api.tavily.com
Auth:     Authorization: Bearer $(chezmoi secret keyring get --service=tavily --user=api_key)
Content:  Content-Type: application/json
Optional: X-Project-ID: <project-id>
```

## Endpoints

### 1. Search — POST /search

Web search with optional AI-generated answer.

```bash
curl -sS -X POST "https://api.tavily.com/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(chezmoi secret keyring get --service=tavily --user=api_key)" \
  -d '{
    "query": "<query>",
    "search_depth": "basic",
    "max_results": 5,
    "include_answer": true,
    "include_raw_content": false,
    "include_images": false
  }'
```

**Key parameters:**

| Parameter | Values | Notes |
|-----------|--------|-------|
| `query` | string | Required |
| `search_depth` | `basic` \| `advanced` \| `fast` \| `ultra-fast` | Default: basic |
| `max_results` | 0–20 | |
| `topic` | `general` \| `news` \| `finance` | |
| `time_range` | `day` \| `week` \| `month` \| `year` | |
| `include_answer` | `false` \| `true` \| `basic` \| `advanced` | |
| `include_raw_content` | `false` \| `true` \| `markdown` \| `text` | |
| `include_domains` / `exclude_domains` | string arrays | Filter sources |

**Response:** `answer`, `results[]` (title, url, content, score), `response_time`, `usage`

### 2. Extract — POST /extract

Pull content from specific URLs.

```bash
curl -sS -X POST "https://api.tavily.com/extract" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(chezmoi secret keyring get --service=tavily --user=api_key)" \
  -d '{
    "urls": ["https://example.com/article"],
    "format": "markdown"
  }'
```

**Key parameters:**

| Parameter | Values | Notes |
|-----------|--------|-------|
| `urls` | string array | Required |
| `query` | string | Rerank chunks by intent |
| `chunks_per_source` | 1–5 | Only with query |
| `extract_depth` | `basic` \| `advanced` | |
| `format` | `markdown` \| `text` | |
| `timeout` | 1–60 | Seconds |

**Response:** `results[]` (url, raw_content), `failed_results[]`, `response_time`

### 3. Map — POST /map

Discover URLs on domain (no content extraction).

```bash
curl -sS -X POST "https://api.tavily.com/map" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(chezmoi secret keyring get --service=tavily --user=api_key)" \
  -d '{
    "url": "https://docs.example.com",
    "max_depth": 1,
    "limit": 50
  }'
```

**Key parameters:**

| Parameter | Values | Notes |
|-----------|--------|-------|
| `url` | string | Required |
| `max_depth` | 1–5 | |
| `max_breadth` | 1+ | |
| `limit` | 1+ | |
| `allow_external` | boolean | Follow external links |
| `instructions` | string | Natural language filter (raises cost) |

**Response:** `base_url`, `results[]` (list of URLs), `response_time`

### 4. Crawl — POST /crawl

Map site and extract content in one call.

```bash
curl -sS -X POST "https://api.tavily.com/crawl" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(chezmoi secret keyring get --service=tavily --user=api_key)" \
  -d '{
    "url": "https://docs.example.com",
    "max_depth": 1,
    "limit": 50,
    "format": "markdown"
  }'
```

**Key parameters:** Same as Map, plus:

| Parameter | Values | Notes |
|-----------|--------|-------|
| `extract_depth` | `basic` \| `advanced` | |
| `format` | `markdown` \| `text` | |
| `chunks_per_source` | 1–5 | Only with instructions |

**Response:** `base_url`, `results[]` (url, raw_content), `response_time`

### 5. Research — POST /research

Multi-step analysis with citations. Async workflow.

**Start research:**

```bash
curl -sS -X POST "https://api.tavily.com/research" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(chezmoi secret keyring get --service=tavily --user=api_key)" \
  -d '{
    "input": "<research question>",
    "model": "auto",
    "stream": false,
    "citation_format": "numbered"
  }'
```

**Response:** `request_id`, `status` (pending)

**Check status:**

```bash
curl -sS -X GET "https://api.tavily.com/research/<request_id>" \
  -H "Authorization: Bearer $(chezmoi secret keyring get --service=tavily --user=api_key)"
```

**Response:** `status` (completed), `content` (report), `sources[]`

**Streaming:** Set `"stream": true` and use `curl -N` for SSE events.

## Defaults

Use conservative defaults unless deeper recall needed:

- `search_depth: basic`
- `max_results: 5`
- `include_raw_content: false`

## Error Handling

| Error | Action |
|-------|--------|
| 401/403 | Verify key in keyring: `chezmoi secret keyring get --service=tavily --user=api_key` |
| Timeout | Reduce `max_depth`/`limit` or use `search_depth: basic` |
| Response too large | Lower `max_results` or `chunks_per_source` |

## Bundled Scripts

### grokipedia.py — Search Grokipedia.com

Domain-scoped search restricted to `grokipedia.com` and `grokxpedia.us` using Tavily's `include_domains` parameter. Equivalent to Google's `site:grokipedia.com` operator.

```bash
# Basic search
uv run <skill_dir>/scripts/grokipedia.py "quantum computing"

# More results
uv run <skill_dir>/scripts/grokipedia.py "Italian cuisine" -n 10

# Include raw page content
uv run <skill_dir>/scripts/grokipedia.py "AI history" --raw

# JSON output for piping
uv run <skill_dir>/scripts/grokipedia.py "neural networks" --json | jq '.results[].url'
```

| Flag | Description |
|------|-------------|
| `query` | Search query (positional, required) |
| `-n, --max-results` | Number of results, 1-20 (default: 5) |
| `--raw` | Include raw page content |
| `--json` | Machine-readable JSON output |
| `--version` | Print version and exit |
