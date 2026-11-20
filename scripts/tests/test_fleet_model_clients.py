import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "authoring"
CLIENTS = (
    "andy/headless/scripts/headless.py",
    "andy/andy-mode/scripts/distill/distill.py",
    "andy/image-creator/scripts/image_creator.py",
    "andy/transcript/scripts/transcript.py",
    "matt/writing-for-agents/scripts/run_evals.py",
)
BRIDGE = {"ModelAliasError", "is_model_alias", "resolve_model_alias"}
END = re.compile(r"^(?!def (?:is_model_alias|resolve_model_alias)\()[^\s#]", re.M)


def client_bridge(path: str) -> dict[str, str]:
    source = (ROOT / path).read_text(encoding="utf-8")
    _, marker, rest = source.partition("\nclass ModelAliasError")
    assert marker, path
    header, _, body = rest.partition("\n")
    end = END.search(body)
    bridge = (
        "class ModelAliasError" + header + "\n" + body[: end.start() if end else None]
    )
    tree = ast.parse(bridge)
    return {
        node.name: ast.dump(node)
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in BRIDGE
    }


def test_standalone_skill_clients_ship_the_same_fleet_bridge() -> None:
    # Skills ship individually. Keep the bridge in sync with Headless so fallback
    # and errors behave the same without a dependency on another public package.
    expected = client_bridge(CLIENTS[0])
    assert set(expected) == BRIDGE
    for client in CLIENTS[1:]:
        assert client_bridge(client) == expected, client
