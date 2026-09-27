# Update the Codex headless reference

When the Codex headless guidance needs a refresh:

1. Read the current [non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode) and [`codex exec` reference](https://learn.chatgpt.com/docs/developer-commands#codex-exec)
2. Compare their relevant behavior with `codex --version`, `codex exec --help`, `codex exec resume --help`, and `codex login status` on the installed CLI
3. Update only the run procedure that changed. Keep the official docs as the flag catalogue and avoid fixed model names or examples that will drift
4. Check the Codex guidance in `../../delegation/MetaSkill.md` and `../../GLOSSARY.md` for conflicting claims, then regenerate `skills/headless/` with `just flatten-skills`
