---
name: "tavily"
description: "Use when a request names Tavily, or when `web-research` reaches level 2."
kind: "general"
configuration-is-needed: true
---

# Tavily REST API

## Overview

Tavily gives LLM-optimized search, content extraction, site mapping, and crawling via REST.

## Quick Reference

| Need | Endpoint | Use Case |
|------|----------|----------|
| Search web | `POST /search` | Find pages, get summaries, optional AI answer |
| Extract from URLs | `POST /extract` | Pull content from specific pages |
| Map site | `POST /map` | Discover all URLs on domain |
| Crawl site | `POST /crawl` | Map + extract in one call |
| Deep research | `POST /research` | Multi-step analysis with citations |

## When NOT to Use

- Local filesystem or repository work; use local tools
- `TAVILY_API_KEY` is missing from fnox (check first)

## Authentication

The key is `TAVILY_API_KEY` in the fnox store (`docs/operations/secrets.md` in pascalandy/dotfiles). Give a command its key with:

```bash
fnox exec --only TAVILY_API_KEY --if-missing error -- <command>
```

`tavily_curl` below sends the key as a header on stdin, so it stays out of argv. It uses `TAVILY_API_KEY` from the environment when set, otherwise fnox, which it finds even under a bare `PATH`, such as T3 Code's on macOS. The endpoint examples call it.

```bash
fnox_run() { for f in "$(command -v fnox)" ~/.local/bin/fnox ~/.local/share/fnox/fnox; do [ -x "$f" ] && { "$f" "$@"; return; }; done; echo 'fnox not found' >&2; return 127; }
tavily_curl() {
  if [ -n "${TAVILY_API_KEY:-}" ]; then
    printf 'Authorization: Bearer %s\n' "$TAVILY_API_KEY" | curl -q -sS -H @- "$@"
  else
    fnox_run exec --only TAVILY_API_KEY --if-missing error -- sh -c \
      'printf "Authorization: Bearer %s\n" "$TAVILY_API_KEY" | curl -q -sS -H @- "$@"' sh "$@"
  fi
}
```

## Base Configuration

```
Base URL: https://api.tavily.com
Auth:     Authorization: Bearer $TAVILY_API_KEY (set by fnox exec)
Content:  Content-Type: application/json
Optional: X-Project-ID: <project-id>
```

## Endpoints

### 1. Search — POST /search

Web search with optional AI-generated answer.

```bash
tavily_curl -X POST "https://api.tavily.com/search" \
  -H "Content-Type: application/json" \
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
tavily_curl -X POST "https://api.tavily.com/extract" \
  -H "Content-Type: application/json" \
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
tavily_curl -X POST "https://api.tavily.com/map" \
  -H "Content-Type: application/json" \
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
tavily_curl -X POST "https://api.tavily.com/crawl" \
  -H "Content-Type: application/json" \
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
tavily_curl -X POST "https://api.tavily.com/research" \
  -H "Content-Type: application/json" \
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
tavily_curl -X GET "https://api.tavily.com/research/<request_id>"
```

**Response:** `status` (completed), `content` (report), `sources[]`

**Streaming:** Set `"stream": true` and use `tavily_curl -N` for SSE events.

## Defaults

Use conservative defaults unless deeper recall needed:

- `search_depth: basic`
- `max_results: 5`
- `include_raw_content: false`

## Error Handling

| Error | Action |
|-------|--------|
| 401/403 | Verify `TAVILY_API_KEY` in fnox: `fnox exec --only TAVILY_API_KEY --if-missing error -- /usr/bin/sh -c 'test -n "${TAVILY_API_KEY:-}"'` |
| Timeout | Reduce `max_depth`/`limit` or use `search_depth: basic` |
| Response too large | Lower `max_results` or `chunks_per_source` |

## Bundled Scripts

### grokipedia.py — Search Grokipedia.com

Domain-scoped search restricted to `grokipedia.com` and `grokxpedia.us` using Tavily's `include_domains` parameter. Equivalent to Google's `site:grokipedia.com` operator.

It writes the AI summary and the results to a Markdown file, then answers in one JSON line that names the file: `{"ok":true,"file":"/abs/path.md"}`. Read that file for the results. Without `--output`, the file is a new `grokipedia-<query>-*.md` in the system temp directory. A failure leaves stdout empty and ends stderr with `{"ok":false,"errors":[…]}`; each error names the command that fixes it.

```bash
# Basic search
uv run <skill_dir>/scripts/grokipedia.py "quantum computing"

# More results
uv run <skill_dir>/scripts/grokipedia.py "Italian cuisine" -n 10

# Include raw page content
uv run <skill_dir>/scripts/grokipedia.py "AI history" --raw

# Write the results to a chosen file
uv run <skill_dir>/scripts/grokipedia.py "neural networks" --output notes/neural-networks.md
```

Run it with `--help` for every flag and exit code.
