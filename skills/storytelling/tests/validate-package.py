# /// script
# requires-python = ">=3.11"
# dependencies = ["markdown-it-py>=3,<5", "pyyaml>=6,<7"]
# ///
"""Check skill metadata, invocation controls, and bundled Markdown links."""

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


def validate_explicit_invocation(
    package: Path, metadata: dict[object, object], runtime: str
) -> None:
    if runtime == "pi":
        if metadata.get("disable-model-invocation") is not True:
            raise ValueError(
                f"{package / 'SKILL.md'}: Pi explicit invocation requires "
                "disable-model-invocation to be the boolean true"
            )
        return

    if runtime != "codex":
        raise ValueError(f"unsupported explicit runtime: {runtime}")

    policy_path = package / "agents/openai.yaml"
    if not policy_path.is_file():
        raise ValueError(
            f"{policy_path}: Codex explicit invocation requires "
            "policy.allow_implicit_invocation to be the boolean false"
        )
    policy_metadata = yaml_mapping(policy_path.read_text(encoding="utf-8"), policy_path)
    policy = policy_metadata.get("policy")
    if (
        not isinstance(policy, dict)
        or policy.get("allow_implicit_invocation") is not False
    ):
        raise ValueError(
            f"{policy_path}: Codex explicit invocation requires "
            "policy.allow_implicit_invocation to be the boolean false"
        )


def validate(package: Path, explicit_runtimes: tuple[str, ...] = ()) -> None:
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
    for runtime in explicit_runtimes:
        validate_explicit_invocation(package, metadata, runtime)

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
    invocation = (
        f"; explicit invocation for {', '.join(explicit_runtimes)}"
        if explicit_runtimes
        else ""
    )
    print(
        f"PASS {package.name}: metadata and links in {len(files)} Markdown files"
        f"{invocation}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--explicit-runtime",
        action="append",
        choices=("codex", "pi"),
        default=[],
        help=(
            "require explicit-only invocation metadata for this target runtime; "
            "repeat for multiple runtimes"
        ),
    )
    parser.add_argument("package", type=Path, help="Skill directory to inspect")
    args = parser.parse_args()
    try:
        validate(args.package.resolve(), tuple(args.explicit_runtime))
    except (OSError, TypeError, ValueError, yaml.YAMLError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
