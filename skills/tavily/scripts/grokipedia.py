#!/usr/bin/env uv run python3
# /// script
# dependencies = [
#     "httpx>=0.27",
#     "rich>=13.0",
# ]
# ///
# -*- coding: utf-8 -*-
"""
Search Grokipedia.com using Tavily API.

Usage:
    uv run grokipedia.py "quantum computing"
    uv run grokipedia.py "Italian cuisine" --max-results 10
    uv run grokipedia.py "AI history" --raw
    uv run grokipedia.py "neural networks" --json | jq '.results[].url'
"""

import argparse
import json
import subprocess
import sys
from typing import Any

import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

__version__ = "0.1.0"

TAVILY_API_URL = "https://api.tavily.com/search"
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"
GROKIPEDIA_BASE = "https://grokipedia.com/page"
SEARCH_DOMAINS = ["grokipedia.com", "grokxpedia.us"]

# Separate consoles: stdout for data, stderr for diagnostics
out = Console()
err = Console(stderr=True)


class ApiKeyError(Exception):
    """Raised when the Tavily API key cannot be retrieved."""


def get_api_key() -> str:
    """Retrieve Tavily API key from macOS keyring via chezmoi.

    Returns:
        The API key string, stripped of whitespace.

    Raises:
        ApiKeyError: If chezmoi is missing, keyring lookup fails, or key is empty.
    """
    try:
        result = subprocess.run(
            [
                "chezmoi",
                "secret",
                "keyring",
                "get",
                "--service=tavily",
                "--user=api_key",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        key = result.stdout.strip()
        if not key:
            raise ApiKeyError(
                "Tavily API key from keyring is empty.\n"
                "  Set it with: chezmoi secret keyring set --service=tavily --user=api_key"
            )
        return key
    except FileNotFoundError as exc:
        raise ApiKeyError(
            "chezmoi not found in PATH.\n"
            "  Install chezmoi: https://www.chezmoi.io/install/"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise ApiKeyError(
            "Could not retrieve Tavily API key from keyring.\n"
            "  Set it with: chezmoi secret keyring set --service=tavily --user=api_key"
        ) from exc


def search_grokipedia(
    query: str,
    max_results: int = 5,
    include_raw: bool = False,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Search grokipedia.com using Tavily API with include_domains filter.

    Args:
        query: Search query string.
        max_results: Maximum number of results (1-20).
        include_raw: Whether to include raw page content.
        api_key: Tavily API key. If None, retrieved from keyring via get_api_key().

    Returns:
        Tavily API response as a dictionary.

    Raises:
        ApiKeyError: If api_key is None and keyring lookup fails.
        httpx.HTTPStatusError: On non-2xx response.
        httpx.RequestError: On connection/timeout failure.
    """
    if api_key is None:
        api_key = get_api_key()

    payload = {
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results,
        "include_answer": True,
        "include_raw_content": include_raw,
        "include_domains": SEARCH_DOMAINS,
        "topic": "general",
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            TAVILY_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()


def normalize_page_title(query: str) -> str:
    """Convert a search query to a Grokipedia URL path segment.

    Follows MediaWiki URL conventions: first letter capitalized,
    spaces replaced with underscores, interior casing preserved.

    Args:
        query: Raw search query string.

    Returns:
        URL-ready page title (e.g., "quantum computing" -> "Quantum_computing").
    """
    title = query.strip()
    if not title:
        return ""
    # Collapse multiple spaces, replace with underscores
    parts = title.split()
    title = "_".join(parts)
    # Capitalize first letter only, preserve the rest
    return title[0].upper() + title[1:]


def extract_exact_page(
    query: str,
    api_key: str | None = None,
) -> dict[str, Any] | None:
    """Try to extract the canonical Grokipedia page matching the query.

    Constructs the URL ``grokipedia.com/page/{Title}`` and uses Tavily's
    /extract endpoint. Returns a search-result-compatible dict if the page
    exists, or None on any failure.

    Args:
        query: Search query to derive the page title from.
        api_key: Tavily API key. If None, retrieved from keyring.

    Returns:
        A dict with keys (title, url, content, score, raw_content) or None.
    """
    if api_key is None:
        api_key = get_api_key()

    title = normalize_page_title(query)
    if not title:
        return None

    canonical_url = f"{GROKIPEDIA_BASE}/{title}"

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                TAVILY_EXTRACT_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"urls": [canonical_url], "format": "markdown"},
            )
            response.raise_for_status()
            data = response.json()

        results = data.get("results", [])
        if not results:
            return None

        raw_content = results[0].get("raw_content") or ""
        # Build a snippet from the first 500 chars of the page
        snippet = raw_content[:500] + "..." if len(raw_content) > 500 else raw_content

        return {
            "title": title.replace("_", " "),
            "url": canonical_url,
            "content": snippet,
            "score": 1.0,  # exact match
            "raw_content": raw_content,
        }

    except (httpx.HTTPStatusError, httpx.RequestError):
        return None


def display_results(data: dict[str, Any], raw: bool = False) -> None:
    """Display search results with rich formatting.

    Args:
        data: Tavily API response dictionary.
        raw: Whether to show raw page content.
    """
    query = data.get("query", "Unknown")
    answer = data.get("answer")
    results = data.get("results", [])

    # Header
    out.print(
        Panel(
            f"[bold cyan]Query:[/bold cyan] {query}\n"
            f"[dim]Domains: {', '.join(SEARCH_DOMAINS)}[/dim]",
            title="[bold green]Grokipedia Search via Tavily[/bold green]",
            border_style="green",
        )
    )

    # AI Answer
    if answer:
        out.print(
            Panel(
                Markdown(answer),
                title="[bold yellow]AI Summary[/bold yellow]",
                border_style="yellow",
            )
        )

    # Results
    if not results:
        out.print("[yellow]No results found on grokipedia.com[/yellow]")
        return

    out.print(f"\n[bold]Found {len(results)} result(s):[/bold]\n")

    for i, result in enumerate(results, 1):
        title = result.get("title") or "No title"
        url = result.get("url") or ""
        content = result.get("content") or ""
        score = result.get("score")

        title_text = Text()
        title_text.append(f"{i}. ", style="bold cyan")
        title_text.append(title, style="bold white underline")
        out.print(title_text)
        out.print(f"   [dim]{url}[/dim]")
        if score is not None:
            out.print(f"   [dim]Relevance: {score:.2f}[/dim]")
        else:
            out.print("   [dim]Relevance: N/A[/dim]")

        if content:
            snippet = content[:300] + "..." if len(content) > 300 else content
            out.print(Panel(snippet, border_style="dim", padding=(0, 2)))

        raw_content = result.get("raw_content") or ""
        if raw and raw_content:
            out.print("[dim]--- Raw Content ---[/dim]")
            out.print(
                raw_content[:500] + "..." if len(raw_content) > 500 else raw_content
            )

        out.print()

    # Footer
    response_time = data.get("response_time")
    if response_time is not None:
        out.print(f"[dim]Response time: {response_time:.2f}s[/dim]")
    else:
        out.print("[dim]Response time: N/A[/dim]")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Search Grokipedia.com using Tavily API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  uv run grokipedia.py "quantum physics"
  uv run grokipedia.py "Italian cuisine" -n 10
  uv run grokipedia.py "AI history" --raw
  uv run grokipedia.py "neural networks" --json | jq '.results[].url'
""",
    )

    parser.add_argument(
        "query",
        help="Search query (e.g., 'quantum computing')",
    )

    parser.add_argument(
        "-n",
        "--max-results",
        type=int,
        default=5,
        help="Maximum number of results (default: 5, max: 20)",
    )

    parser.add_argument(
        "--raw",
        action="store_true",
        help="Include raw content from pages",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output raw JSON instead of formatted results",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point.

    Returns:
        Exit code: 0 success, 1 runtime error, 2 validation error.
    """
    args = parse_arguments()

    # Validate inputs before doing any work
    query = args.query.strip()
    if not query:
        err.print("[red]Error: query must not be empty[/red]")
        err.print('  uv run grokipedia.py "your search terms"')
        return 2

    if args.max_results < 1 or args.max_results > 20:
        err.print(
            f"[red]Error: --max-results must be 1-20, got {args.max_results}[/red]"
        )
        err.print('  uv run grokipedia.py "your query" -n 5')
        return 2

    try:
        api_key = get_api_key()

        data = search_grokipedia(
            query=query,
            max_results=args.max_results,
            include_raw=args.raw,
            api_key=api_key,
        )

        # Hybrid lookup: if the canonical page isn't in search results,
        # try extracting it directly and prepend it.
        title = normalize_page_title(query)
        canonical_url = f"{GROKIPEDIA_BASE}/{title}"
        existing_urls = {r.get("url", "").lower() for r in data.get("results", [])}

        if canonical_url.lower() not in existing_urls:
            exact = extract_exact_page(query, api_key=api_key)
            if exact is not None:
                data.setdefault("results", []).insert(0, exact)

        if args.json_output:
            print(json.dumps(data, indent=2))
        else:
            display_results(data, raw=args.raw)

        return 0

    except ApiKeyError as e:
        err.print(f"[red]Error: {e}[/red]")
        return 1

    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        err.print(f"[red]Error: Tavily API returned HTTP {status}[/red]")
        if status in (401, 403):
            err.print(
                "  Verify API key: chezmoi secret keyring get --service=tavily --user=api_key"
            )
        elif status == 429:
            err.print("  Rate limited. Wait a moment and retry.")
        else:
            err.print(f"  Response: {e.response.text[:200]}")
        return 1

    except httpx.RequestError as e:
        err.print("[red]Error: Could not reach Tavily API[/red]")
        err.print(f"  {e}")
        err.print("  Check your internet connection and try again.")
        return 1

    except KeyboardInterrupt:
        err.print("\n[dim]Interrupted[/dim]")
        return 130


if __name__ == "__main__":
    sys.exit(main())
