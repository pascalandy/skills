# /// script
# dependencies = ["PyYAML>=6.0,<7"]
# ///
"""Validate Matt mode's routed package and pinned upstream imports."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections.abc import Hashable
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

TOOLS = Path(__file__).resolve().parent
DEFAULT_ROOT = TOOLS.parent.parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


layout = load_module("meta_skill_layout", TOOLS / "check_meta_skill_layout.py")
updater = load_module("matt_mode_updater", TOOLS / "update_matt_mode.py")


class UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(
        self, node: MappingNode, deep: bool = False
    ) -> dict[Hashable, Any]:
        self.flatten_mapping(node)
        mapping: dict[Hashable, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in mapping:
                raise ConstructorError(
                    None,
                    None,
                    "mapping keys must be unique strings",
                    key_node.start_mark,
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def parse_metadata(
    text: str, label: str, errors: list[str]
) -> dict[str, object] | None:
    try:
        value = yaml.load(text, Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        errors.append(f"{label}: invalid YAML: {error}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label}: metadata must be a mapping")
        return None
    return value


def validate_entry(
    package: Path,
    package_name: str,
    expected_link: str | None,
    errors: list[str],
) -> set[str]:
    entry = package / "SKILL.md"
    scanner_files = sorted(path for path in package.rglob("SKILL.md") if path.is_file())
    if scanner_files != [entry]:
        found = (
            ", ".join(path.relative_to(package).as_posix() for path in scanner_files)
            or "none"
        )
        errors.append(
            f"{package_name}: expected exactly one root SKILL.md; found: {found}"
        )
    if not entry.is_file() or entry.is_symlink():
        errors.append(f"{package_name}: root SKILL.md is missing")
        return set()

    label = f"{package_name}/SKILL.md"
    layout.validate_instruction_file(entry, label, errors)
    text = layout.read_utf8(entry, label, errors)
    links: set[str] = set()
    if text is not None:
        frontmatter, _ = layout.split_frontmatter_text(text, label, errors)
        metadata = parse_metadata("\n".join(frontmatter), label, errors)
        if metadata is not None:
            if metadata.get("name") != package_name:
                errors.append(f'{label}: require name: "{package_name}"')
            description = metadata.get("description")
            if not isinstance(description, str) or not description.strip():
                errors.append(f"{label}: require a non-empty description string")
        links = {
            target.partition("#")[0] for target in layout.markdown_link_targets(text)
        }
        if expected_link is not None and expected_link not in links:
            errors.append(f"{label}: missing upstream body link: {expected_link}")
    return links


def validate_mapping_shapes(registry, errors: list[str]) -> tuple[set[str], set[str]]:
    internal_entries: set[str] = set()
    shared_names: set[str] = set()
    for mapping in registry.mappings:
        if mapping.kind == "internal":
            expected = PurePosixPath("matt-mode/playbooks") / mapping.name
            if mapping.destination != expected or mapping.entry != f"{mapping.name}.md":
                errors.append(
                    f"lock mapping {mapping.name}: internal destination or entry is inconsistent"
                )
            internal_entries.add(
                str((mapping.destination / mapping.entry).relative_to("matt-mode"))
            )
        else:
            expected = PurePosixPath(mapping.name) / "references/upstream"
            if mapping.destination != expected or mapping.entry != f"{mapping.name}.md":
                errors.append(
                    f"lock mapping {mapping.name}: shared destination or entry is inconsistent"
                )
            shared_names.add(mapping.name)
    return internal_entries, shared_names


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    if root.is_symlink() or not root.is_dir():
        return [f"expected a non-symlink Matt skill bucket: {root}"]
    try:
        registry = updater.parse_registry(root)
    except updater.ImportError as error:
        return [str(error)]

    internal_entries, shared_names = validate_mapping_shapes(registry, errors)
    package_names = {"matt-mode", *shared_names}
    for package_name in sorted(package_names):
        package = root / package_name
        if not package.is_dir() or package.is_symlink():
            errors.append(f"missing sibling package: {package_name}")
            continue
        if not layout.validate_no_symlinks(package, errors):
            continue
        expected_link = None
        if package_name != "matt-mode":
            expected_link = f"references/upstream/{package_name}.md"
        links = validate_entry(package, package_name, expected_link, errors)
        if package_name == "matt-mode":
            routed = {target for target in links if target.startswith("playbooks/")}
            if routed != internal_entries:
                missing = ", ".join(sorted(internal_entries - routed)) or "none"
                unexpected = ", ".join(sorted(routed - internal_entries)) or "none"
                errors.append(
                    "matt-mode/SKILL.md: route table disagrees with lock; "
                    f"missing: {missing}; unexpected: {unexpected}"
                )
        layout.validate_markdown_links(package, errors)
        layout.validate_portability(package, errors)
        layout.validate_asset_modes(package, [], [], errors)

    errors.extend(updater.verify_imports(root))
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        type=Path,
        nargs="?",
        default=DEFAULT_ROOT,
        metavar="BUCKET",
        help="Matt skill bucket (default: repository source)",
    )
    args = parser.parse_args()
    try:
        errors = validate(args.root.absolute())
    except OSError as error:
        errors = [f"cannot inspect {args.root}: {error}"]
    if errors:
        print("Matt mode packages invalid:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    registry = updater.parse_registry(args.root.absolute())
    _, shared_names = validate_mapping_shapes(registry, [])
    route_count = sum(mapping.kind == "internal" for mapping in registry.mappings)
    package_count = len(shared_names) + 1
    print(
        f"OK: Matt mode packages valid: {args.root.absolute()} "
        f"(packages={package_count}, entrypoints={package_count}, "
        f"routes={route_count}, imports={len(registry.files)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
