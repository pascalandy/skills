# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Render fenced Mermaid examples with mmdc; optionally build an offline gallery.

Usage: uv run render_examples.py SKILL.md references/*.md --output /tmp/mermaid
       Add --gallery and, if needed, --mmdc /path/to/mmdc
       uv run render_examples.py references/data-perspectives.md --output /tmp/data --gallery

Uses the bundled black-background theme; --config overrides it. Diagram frontmatter
can override individual family settings.
"""

import argparse
import base64
import html
import re
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class Example:
    path: Path
    line: int
    heading: str
    source: str
    prose: str
    after: str = ""


def extract(path: Path) -> list[Example]:
    """Read top-level backtick or tilde fences, ignoring nested example fences."""
    examples: list[Example] = []
    heading = path.stem
    fence = ""
    mermaid = False
    source: list[str] = []
    prose: list[str] = []
    start = 0
    after_diagram = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if fence:
            if re.fullmatch(
                r" {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*", line
            ):
                if mermaid:
                    examples.append(
                        Example(
                            path,
                            start,
                            heading,
                            "\n".join(source) + "\n",
                            "\n".join(prose).strip(),
                        )
                    )
                    prose = []
                    after_diagram = True
                fence = ""
            elif mermaid:
                source.append(line)
            continue
        opening = re.fullmatch(r" {0,3}(`{3,}|~{3,})(.*)", line)
        if opening:
            if after_diagram:
                examples[-1] = replace(examples[-1], after="\n".join(prose).strip())
                prose = []
                after_diagram = False
            fence = opening[1]
            mermaid = opening[2].strip() == "mermaid"
            source = []
            start = number + 1
        else:
            title = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
            if title:
                if after_diagram:
                    examples[-1] = replace(examples[-1], after="\n".join(prose).strip())
                    after_diagram = False
                heading = title[1]
                prose = []
            else:
                prose.append(line)
    if fence and mermaid:
        raise ValueError(f"{path}:{start}: unclosed Mermaid fence")
    if after_diagram:
        examples[-1] = replace(examples[-1], after="\n".join(prose).strip())
    return examples


def paragraphs(text: str) -> str:
    """Escape prose, allowing only HTTPS Markdown links as active markup."""
    rendered = []
    for paragraph in re.split(r"\n\s*\n", text.replace("**", "").replace("`", "")):
        if not paragraph.strip():
            continue
        pieces = []
        end = 0
        for link in re.finditer(r"\[([^\]]+)\]\((https://[^\s)]+)\)", paragraph):
            pieces.append(html.escape(paragraph[end : link.start()]))
            pieces.append(
                f'<a target="_blank" rel="noopener noreferrer" href="{html.escape(link[2], quote=True)}">{html.escape(link[1])}</a>'
            )
            end = link.end()
        pieces.append(html.escape(paragraph[end:]))
        rendered.append('<p class="explanation">' + "".join(pieces) + "</p>")
    return "".join(rendered)


def gallery(results: list[tuple[Example, Path, str]], output: Path) -> None:
    sections = []
    for example, svg, error in results:
        label = html.escape(example.heading)
        location = html.escape(f"{example.path}:{example.line}")
        explanation = paragraphs(example.prose)
        if error:
            picture = f'<p class="error">Échec du rendu : {html.escape(error)}</p>'
        else:
            encoded = base64.b64encode(svg.read_bytes()).decode("ascii")
            picture = f'<img alt="{label}" src="data:image/svg+xml;base64,{encoded}">'
        sections.append(
            f"<section><h2>{label}</h2>{explanation}{picture}"
            f"{paragraphs(example.after)}"
            f"<details><summary>Source Mermaid</summary><p>{location}</p><pre><code>"
            f"{html.escape(example.source)}</code></pre></details></section>"
        )
    output.write_text(
        '<!doctype html><html lang="fr"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Regards nouveaux avec Mermaid</title><style>"
        "body{background:#000;color:#fff;font:16px system-ui;margin:0 auto;"
        "max-width:1400px;padding:32px}section{padding:24px 0;border-top:1px solid #51576d}"
        "img{display:block;max-width:100%;max-height:650px;width:auto;height:auto;margin:24px 0}"
        "a{color:#8caaee}"
        "pre{overflow:auto;padding:16px;background:#181818}summary{cursor:pointer}"
        ".error{color:#e78284}.explanation{white-space:pre-line;line-height:1.5}"
        "h2{font-size:24px}</style><h1>Regards nouveaux avec Mermaid</h1>"
        + "\n".join(sections)
        + "</html>\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="Markdown input files")
    parser.add_argument("--output", required=True, type=Path, help="Artifact directory")
    parser.add_argument("--mmdc", default="mmdc", help="Mermaid CLI executable path")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "assets/theme.json",
        help="Mermaid JSON configuration file (default: bundled assets/theme.json)",
    )
    parser.add_argument(
        "--width", type=int, default=1400, help="Render width in pixels (default: 1400)"
    )
    parser.add_argument(
        "--gallery", action="store_true", help="Write offline index.html"
    )
    args = parser.parse_args()
    if args.width < 1:
        parser.error("--width must be positive")
    try:
        examples = [example for path in args.files for example in extract(path)]
        if not examples:
            parser.error("No Mermaid fenced blocks found")
        args.output.mkdir(parents=True, exist_ok=True)
        results: list[tuple[Example, Path, str]] = []
        for index, example in enumerate(examples, 1):
            stem = f"{index:03d}-{example.path.stem}-L{example.line}"
            source = args.output / f"{stem}.mmd"
            svg = args.output / f"{stem}.svg"
            source.write_text(example.source, encoding="utf-8")
            svg.unlink(missing_ok=True)
            rendered = subprocess.run(
                [
                    args.mmdc,
                    "-i",
                    str(source),
                    "-o",
                    str(svg),
                    "-t",
                    "dark",
                    "-b",
                    "#000000",
                    "-w",
                    str(args.width),
                ]
                + (["-c", str(args.config)] if args.config else []),
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            error = ""
            if rendered.returncode or not svg.is_file():
                error = (rendered.stderr or rendered.stdout or "No SVG output").strip()
            results.append((example, svg, error))
            print(
                f"{'FAIL' if error else 'PASS'} {example.path}:{example.line} -> {svg}"
            )
            if error:
                print(error, file=sys.stderr)
        if args.gallery:
            gallery(results, args.output / "index.html")
        failed = sum(bool(error) for _, _, error in results)
        print(f"{len(results) - failed}/{len(results)} examples rendered")
        return 1 if failed else 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
