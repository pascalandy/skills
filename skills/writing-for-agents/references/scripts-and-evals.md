# Scripts and evaluations

Each `BP_` section explains one best practice listed in `SKILL.md`.

## BP_17 Scripts for repeatable results

When an operation must give the same result every run, such as parsing, validating, converting, or counting, ship a script and tell the agent to run it. Prose makes the agent redo the work each time; a script does it the same way every time and costs no context until its output:

```markdown
## Fillable fields

Run from this skill's folder: `uv run scripts/extract_fields.py <input.pdf> <fields.json>`
```

A good script:

- Solves the problem instead of handing it back to the agent
- Explains each error: what failed, then the command that fixes it
- Justifies every constant
- Documents its usage in `--help`
- Writes every path with forward slashes

## BP_18 Prerequisites named

Name each tool a step needs, how to install it, and how to confirm it is available, such as `uv --version`, before the first step that uses it:

- Assumes the tool: "Use the pdf library to process the file."
- Names it: "Requires `uv` ([install](https://docs.astral.sh/uv/getting-started/installation/)); `uv --version` confirms it. Run `uv run --with pypdf scripts/extract.py file.pdf`."

A Python script with an inline dependency block (PEP 723) installs its own packages under `uv run`.

## BP_20 Evaluations first

Build evaluations before writing extensive instructions, so the skill solves observed failures instead of imagined ones:

1. **Find the gaps**: run an agent on representative tasks without the skill, and note each failure or missing piece of context
2. **Write three scenarios** that test those gaps
3. **Record a baseline**: how the agent does without the skill, or with its current version when you improve one
4. **Write the minimum**: just enough instruction to close the gaps and pass the scenarios
5. **Iterate**: rerun the scenarios, compare with the baseline, and refine

Keep the scenarios in the skill's `evals/evals.json`, one object per scenario:

```json
{
  "skills": ["pdf-processing"],
  "setup": ["mkdir test-files", "cp \"$EVALS/fixtures/document.pdf\" test-files/"],
  "query": "Extract all text from this PDF file and save it to output.txt",
  "files": ["test-files/document.pdf"],
  "expected_behavior": [
    "Reads the PDF with a PDF library or command-line tool",
    "Extracts the text of every page without missing any",
    "Saves the text to output.txt in a readable format"
  ]
}
```

`setup` lists the shell commands that build the scenario's folder; `$EVALS` names the `evals` folder. Give a scenario that needs a remote a local bare repository: runs carry no GitHub or git credentials. Name a fixture so no agent or script mistakes it for a live file, such as `agents-md.md` for an `AGENTS.md` or `SKILL.md.txt` for a `SKILL.md`, and let `setup` copy it to the real name.

Run the scenarios with the eval runner in `SKILL.md`. It gives each scenario a fresh session on every agent it targets, with the skill copied from a git ref and the installed copies hidden, so a run never tests the wrong version.
