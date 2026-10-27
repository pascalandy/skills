"""Exercise rendering at the CLI boundary with the two mmdc sizing contracts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "render_examples.py"


@pytest.mark.parametrize("option", ["--width", "--size"])
@pytest.mark.parametrize("width", [None, 920])
def test_renders_with_supported_sizing_option(
    tmp_path: Path, option: str, width: int | None
) -> None:
    source = tmp_path / "examples.md"
    source.write_text(
        "```mermaid\nsequenceDiagram\nA->>B: ready\n```\n", encoding="utf-8"
    )
    mmdc = tmp_path / "mmdc"
    mmdc.write_text(
        f"#!{sys.executable}\n"
        "import json, pathlib, sys\n"
        f"option = {option!r}\n"
        "if '--help' in sys.argv:\n"
        "    print('Usage: mmdc\\n  ' + option + ' <pixels>\\n  -s, --scale <scale>')\n"
        "    sys.exit(0)\n"
        "for flag in ('-w', '--width', '--size', '-s', '--scale'):\n"
        "    if flag in sys.argv and flag not in (('-w', '--width') if option == '--width' else (option,)):\n"
        "        sys.exit('error: unknown option ' + flag)\n"
        "output = pathlib.Path(sys.argv[sys.argv.index('-o') + 1])\n"
        "size_flag = option if option in sys.argv else '-w'\n"
        "output.write_text('<svg>' + sys.argv[sys.argv.index(size_flag) + 1] + '</svg>')\n"
        "output.with_suffix('.args.json').write_text(json.dumps(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    mmdc.chmod(0o755)
    output = tmp_path / "out"
    result = subprocess.run(
        [
            "uv",
            "run",
            str(SCRIPT),
            str(source),
            "--output",
            str(output),
            "--mmdc",
            str(mmdc),
        ]
        + (["--width", str(width)] if width is not None else []),
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    svg = output / "001-examples-L2.svg"
    assert json.loads(result.stdout) == {"ok": True, "files": [str(svg)]}
    assert svg.read_text(encoding="utf-8") == f"<svg>{width or 1400}</svg>"
    assert (
        svg.with_suffix(".mmd").read_text(encoding="utf-8")
        == "sequenceDiagram\nA->>B: ready\n"
    )
    args = json.loads(svg.with_suffix(".args.json").read_text(encoding="utf-8"))
    assert args[args.index("-b") + 1] == "#000000"
    assert Path(args[args.index("-c") + 1]).name == "theme.json"
