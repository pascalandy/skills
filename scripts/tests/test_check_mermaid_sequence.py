"""Guard sequence text at original Markdown lines, without rendering diagrams."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import check_mermaid_sequence as checker
import pytest

SCRIPT = Path(checker.__file__)
HISTORICAL = Path(__file__).parent / "fixtures/mermaid_sequence/carpaccio-33777f21.md"
PRELUDE = """# Example

```mermaid
---
title: "YAML # and ; are not sequence text"
---
%% A comment with ; and #
%%{init: {
  "theme": "base"
}}%%
sequenceDiagram
"""


def test_historical_cli_reports_exact_original_lines_and_failure_channels() -> None:
    result = subprocess.run(
        ["uv", "run", str(SCRIPT), str(HISTORICAL)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    report = json.loads(result.stderr.splitlines()[-1])
    assert report == {
        "ok": False,
        "errors": [
            (
                f"{HISTORICAL.relative_to(checker.ROOT)}:88: bare ';' in sequence block label; write ';' as '#59;' "
                "and '#' as '#35;', then rerun just check-mermaid-sequence"
            ),
            (
                f"{HISTORICAL.relative_to(checker.ROOT)}:92: bare '#' in sequence message; write ';' as '#59;' "
                "and '#' as '#35;', then rerun just check-mermaid-sequence"
            ),
        ],
    }


MESSAGES = [
    f"A{arrow}{activation}B: "
    for arrow in ("->>", "-->>", "->", "-->", "-x", "--x", "-)", "--)")
    for activation in ("", "+", "-")
] + ["A->>()B: ", "A()->>B: "]
NOTES = [
    f"{note} {location}: "
    for note in ("Note", "note", "NOTE")
    for location in ("over A,B", "left of A", "right of B")
]
BLOCKS = [
    f"{keyword} "
    for keyword in (
        "alt",
        "else",
        "opt",
        "loop",
        "par",
        "and",
        "critical",
        "option",
        "break",
    )
]


@pytest.mark.parametrize("prefix", MESSAGES + NOTES + BLOCKS)
@pytest.mark.parametrize("character", [";", "#"])
def test_all_text_forms_flag_bare_characters_after_entities(
    prefix: str, character: str
) -> None:
    text = PRELUDE + prefix + "PR#35;35 #59; done" + character + " extra\n```\n"
    errors, count = checker.check_text(text, "diagram.md")
    assert count == 1
    assert len(errors) == 1
    assert errors[0].startswith(f"diagram.md:12: bare {character!r} in sequence ")
    assert checker.check_text(
        text.replace(character + " extra", " extra"), "diagram.md"
    ) == ([], 1)


def test_fences_and_non_sequence_controls(tmp_path: Path) -> None:
    text = """`````markdown
```mermaid
sequenceDiagram
A->>B: nested #;
```
`````

~~~mermaid
%%{init: {"theme": "base"}}%%
sequenceDiagram
note over A,B: PR#35;35#59; ready
A-->>B: #word; #59; #35;
~~~

```mermaid
flowchart LR
A["# ;"] --> B
```

````markdown
```mermaid
sequenceDiagram
A->>B: longer outer fence #;
```
````
"""
    path = tmp_path / "examples.md"
    path.write_text(text, encoding="utf-8")
    result = subprocess.run(
        ["uv", "run", str(SCRIPT), "--verbose", str(path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0
    assert result.stdout == '{"ok":true}\n'
    assert result.stderr == "checked 1 files containing 1 sequence blocks\n"
    errors, count = checker.check_text(
        text.replace("PR#35;35#59; ready", "PR#35;35#59; ready#"), "examples.md"
    )
    assert count == 1
    assert len(errors) == 1
    assert ":11: bare '#' in sequence note" in errors[0]
