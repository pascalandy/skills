# /// script
# requires-python = ">=3.11"
# dependencies = ["markdown-it-py>=3,<5", "pyyaml>=6,<7"]
# ///
"""Check skill metadata, agent invocation, and bundled Markdown links."""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token


def body(text: str) -> str:
    return re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)


def markdown_tokens(text: str) -> list[Token]:
    parser = MarkdownIt()
    # Collect schemes suppressed by rendering so portability checks can reject them.
    parser.validateLink = lambda url: True
    return parser.parse(body(text))


def heading_ids(text: str) -> set[str]:
    tokens = markdown_tokens(text)
    anchors: set[str] = set()
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        content = "".join(
            child.content
            for child in tokens[index + 1].children or []
            if child.type in {"text", "code_inline"}
        )
        base = re.sub(r"[^\w\s-]", "", content.lower()).replace(" ", "-")
        anchor = base
        suffix = 0
        while anchor in anchors:
            suffix += 1
            anchor = f"{base}-{suffix}"
        anchors.add(anchor)
    return anchors


def yaml_mapping(text: str, label: Path) -> dict[object, object]:
    value: object = yaml.safe_load(text)
    if not isinstance(value, dict):
        raise TypeError(f"{label}: YAML must be a mapping")
    return value


def validate_agent_invocation(package: Path, metadata: dict[object, object]) -> None:
    if metadata.get("disable-model-invocation") is True:
        raise ValueError(f"{package / 'SKILL.md'}: agent invocation must stay enabled")
    policy_path = package / "agents/openai.yaml"
    if not policy_path.is_file():
        return
    policy_metadata = yaml_mapping(policy_path.read_text(encoding="utf-8"), policy_path)
    policy = policy_metadata.get("policy")
    if isinstance(policy, dict) and policy.get("allow_implicit_invocation") is False:
        raise ValueError(f"{policy_path}: agent invocation must stay enabled")


def validate(package: Path) -> None:
    entry = package / "SKILL.md"
    text = entry.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if match is None:
        raise ValueError(f"{entry}: missing YAML frontmatter")
    metadata = yaml_mapping(match[1], entry)
    name = metadata.get("name")
    description = metadata.get("description")
    if (
        not isinstance(name, str)
        or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
        or len(name) >= 64
        or name != package.name
    ):
        raise ValueError(f"{entry}: name must match its lowercase skill directory")
    if not isinstance(description, str) or not description.strip():
        raise ValueError(f"{entry}: description must be a nonempty string")
    validate_agent_invocation(package, metadata)

    files = sorted(package.rglob("*.md"))
    for path in files:
        tokens = markdown_tokens(path.read_text(encoding="utf-8"))
        for token in tokens:
            for child in token.children or []:
                href = child.attrGet("href") or child.attrGet("src")
                if not isinstance(href, str) or not href:
                    continue
                url = urlsplit(href)
                if url.scheme and url.scheme not in {"https", "http", "mailto"}:
                    raise ValueError(f"{path}: nonportable link scheme: {href}")
                if url.scheme or url.netloc:
                    continue
                local = Path(unquote(url.path))
                target = (path.parent / local).resolve() if url.path else path
                if local.is_absolute() or not target.is_relative_to(package):
                    raise ValueError(f"{path}: link leaves the package: {href}")
                if not target.exists():
                    raise ValueError(f"{path}: broken local link: {href}")
                if url.fragment and target.suffix == ".md":
                    anchors = heading_ids(target.read_text(encoding="utf-8"))
                    if unquote(url.fragment) not in anchors:
                        raise ValueError(f"{path}: missing heading: {href}")
    print(f"PASS {package.name}: metadata and links in {len(files)} Markdown files")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="Skill directory to inspect")
    args = parser.parse_args()
    try:
        validate(args.package.resolve())
    except (OSError, TypeError, ValueError, yaml.YAMLError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
