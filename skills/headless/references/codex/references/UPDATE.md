# Update the Codex headless reference

When the Codex headless guidance needs a refresh:

1. Read the current [non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode) and [`codex exec` reference](https://learn.chatgpt.com/docs/developer-commands#codex-exec)
2. Compare their relevant behavior with `codex --version`, `codex exec --help`, `codex review --help`, `codex exec review --help`, `codex exec resume --help`, and `codex login status` on the installed CLI
3. Check the [Codex model list](https://learn.chatgpt.com/docs/models) and `codex debug models --help` before changing model examples. Update the [flag lookup](FLAGS.md) when the installed and official flag lists change
4. Check the Codex guidance in `../../delegation/MetaSkill.md` and `../../GLOSSARY.md` for conflicting claims, then regenerate `skills/headless/` with `just flatten-skills`
