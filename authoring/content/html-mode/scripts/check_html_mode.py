# /// script
# dependencies = []
# ///
"""Validate html-mode's reveal.js presentation package and active references."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
PIN_RE = re.compile(
    r"^Current reveal\.js pin: `(?P<pin>\d+\.\d+\.\d+)`\.$", re.MULTILINE
)
CDN_RE = re.compile(
    r"https://cdn\.jsdelivr\.net/npm/reveal\.js@(?P<version>[^/\s\"'`)]+)/(?P<path>[^\s\"'`)]+)"
)
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\((?P<target>[^)]+)\)")
AGENT_SPECIFIC_RE = re.compile(
    r"\b(?:claude|office-mcp)\b|^models:\s*$", re.IGNORECASE | re.MULTILINE
)


class DeckParser(HTMLParser):
    """Collect observable structure from the reusable deck template."""

    def __init__(self) -> None:
        super().__init__()
        self.html_lang: str | None = None
        self.viewport: str | None = None
        self.stylesheets: list[str] = []
        self.scripts: list[str] = []
        self.section_ids: list[str | None] = []
        self.fragment_count = 0
        self.internal_links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.html_lang = values.get("lang")
        elif tag == "meta" and values.get("name") == "viewport":
            self.viewport = values.get("content")
        elif tag == "link" and values.get("rel") == "stylesheet":
            if href := values.get("href"):
                self.stylesheets.append(href)
        elif tag == "script":
            if src := values.get("src"):
                self.scripts.append(src)
        elif tag == "section":
            self.section_ids.append(values.get("id"))

        classes = (values.get("class") or "").split()
        if "fragment" in classes:
            self.fragment_count += 1

        if tag == "a" and (href := values.get("href")) and href.startswith("#/"):
            self.internal_links.append(href[2:])


def read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        errors.append(f"{path}: cannot read file: {error}")
        return ""


def validate_links(package: Path, errors: list[str]) -> None:
    for source in sorted(package.rglob("*.md")):
        text = read_text(source, errors)
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = match.group("target").split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            destination = (source.parent / target).resolve()
            if not destination.exists():
                errors.append(
                    f"{source.relative_to(package)}: unresolved Markdown link: {target}"
                )


def validate_package(root: Path, errors: list[str]) -> tuple[int, int, str | None]:
    package = root
    entry = package / "SKILL.md"
    playbook = package / "playbooks/slides.md"
    artifact = package / "playbooks/artifact.md"
    documents = package / "references/documents-and-presentations.md"
    template = package / "assets/slides-template.html"

    required = (entry, playbook, artifact, documents, template)
    for path in required:
        if not path.is_file():
            errors.append(f"source: required file is missing: {path.relative_to(root)}")
    if any(not path.is_file() for path in required):
        return 0, 0, None

    entry_text = read_text(entry, errors)
    playbook_text = read_text(playbook, errors)
    artifact_text = read_text(artifact, errors)
    documents_text = read_text(documents, errors)
    template_text = read_text(template, errors)

    expected_routes = {
        "Wireframe": "playbooks/wireframe.md",
        "Prototype": "playbooks/prototype.md",
        "Plan": "playbooks/plan.md",
        "Diagram": "playbooks/diagram.md",
        "Slides": "playbooks/slides.md",
        "Artifact": "playbooks/artifact.md",
    }
    for label, target in expected_routes.items():
        if f"[{label}]({target})" not in entry_text:
            errors.append(f"routing: html-mode is missing {label} -> {target}")
    if "External dependencies require user permission except" not in entry_text:
        errors.append(
            "routing: reveal.js CDN exception must preserve the shared default"
        )
    if "[slides playbook](slides.md)" not in artifact_text:
        errors.append("routing: generic artifact playbook does not defer to slides.md")
    if "[slides playbook](../playbooks/slides.md)" not in documents_text:
        errors.append("routing: document reference does not defer to slides.md")

    pin_match = PIN_RE.search(playbook_text)
    pin = pin_match.group("pin") if pin_match else None
    if pin is None:
        errors.append("slides: missing exact reveal.js semantic-version pin")

    package_text = "\n".join(
        read_text(path, errors)
        for path in sorted(package.rglob("*"))
        if path.is_file() and path.suffix in {".html", ".md"}
    )
    portable_text = f"{entry_text}\n{playbook_text}\n{template_text}"
    if AGENT_SPECIFIC_RE.search(portable_text):
        errors.append("portability: agent, model, or MCP-specific metadata remains")

    cdn_matches = list(CDN_RE.finditer(package_text))
    if pin is not None:
        for match in cdn_matches:
            version = match.group("version")
            if version != pin:
                errors.append(
                    f"reveal.js CDN URL is not pinned to {pin}: @{version}/{match.group('path')}"
                )

    parser = DeckParser()
    parser.feed(template_text)

    if parser.html_lang is None:
        errors.append("template: html lang is missing")
    if parser.viewport is None:
        errors.append("template: viewport metadata is missing")

    if pin is not None:
        expected_stylesheets = {
            f"https://cdn.jsdelivr.net/npm/reveal.js@{pin}/dist/reveal.css",
            f"https://cdn.jsdelivr.net/npm/reveal.js@{pin}/dist/theme/black.css",
        }
        expected_scripts = {
            f"https://cdn.jsdelivr.net/npm/reveal.js@{pin}/dist/reveal.js"
        }
        if set(parser.stylesheets) != expected_stylesheets:
            errors.append(
                "template: expected only pinned reveal.js core and black theme CSS"
            )
        if set(parser.scripts) != expected_scripts:
            errors.append("template: expected only pinned reveal.js core JavaScript")
        if any("/plugin/" in url for url in parser.stylesheets + parser.scripts):
            errors.append(
                "template: optional reveal.js plugins must load only on demand"
            )

    section_ids = [section_id for section_id in parser.section_ids if section_id]
    if len(section_ids) != len(parser.section_ids):
        errors.append("template: every slide section needs a stable ID")
    if len(section_ids) != len(set(section_ids)):
        errors.append("template: slide IDs must be unique")
    if parser.fragment_count == 0:
        errors.append("template: witness deck needs a fragment sequence")
    missing_targets = sorted(set(parser.internal_links) - set(section_ids))
    if missing_targets:
        errors.append(
            f"template: broken direct slide links: {', '.join(missing_targets)}"
        )

    expected_config = (
        "controls: true",
        "progress: true",
        'slideNumber: "c/t"',
        "hash: true",
        "fragmentInURL: true",
        "keyboard: true",
        "touch: true",
        "loop: false",
        "scrollActivationWidth: 700",
        'scrollLayout: "compact"',
        "scrollProgress: true",
    )
    for setting in expected_config:
        if setting not in template_text:
            errors.append(f"template: missing required reveal.js setting: {setting}")
    for requirement in (
        "prefers-reduced-motion: reduce",
        'transition: reduceMotion ? "none" : "fade"',
        "--background: #000",
        "--foreground: #fff",
        "body.reveal-viewport",
    ):
        if requirement not in template_text:
            errors.append(
                f"template: missing theme or motion requirement: {requirement}"
            )

    html_files = sorted(package.rglob("*.html"))
    if html_files != [template]:
        errors.append("package: slides template must be the only bundled HTML file")

    validate_links(package, errors)
    return len(section_ids), parser.fragment_count, pin


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="html-mode package root to validate",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    errors: list[str] = []

    slides, fragments, pin = validate_package(root, errors)

    if errors:
        print("html-mode validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(
        "html-mode presentation package OK "
        f"(reveal.js={pin}, slides={slides}, fragments={fragments})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
