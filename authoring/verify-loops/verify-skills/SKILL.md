---
name: "verify-skills"
description: "Use when proving that `just compile-skills`, `just install-skills`, or `just skills-discover` in the skills repository works on this machine, such as after changing their scripts or adding, renaming, or moving a skill, without writing to the live agent folders."
kind: "dev"
---

# Verify skills

Drive the skills repository's real `just` recipes against a checkout, with the installer pointed at a test home instead of the real one. A run lives in its own folder under `/var/tmp`, keeps its evidence under `~/.local/state/verify-skills/runs/`, and ends by deleting the run folder. The live agent folders, such as `~/.claude/skills`, stay untouched.

## Launch

Run from inside the checkout under test. The block writes `$RUN/env` and prints the run folder. Each later block loads that file in a subshell, so the test home never leaks into another command. When your shell does not keep variables between commands, start each block by setting `RUN` to the printed path.

```bash
CHECKOUT=$(git rev-parse --show-toplevel) &&
RUN=$(mktemp -d "/var/tmp/verify-skills.$(date +%Y%m%d-%H%M%S).XXXX") &&
EVIDENCE="${XDG_STATE_HOME:-$HOME/.local/state}/verify-skills/runs/${RUN##*/verify-skills.}" &&
mkdir -p "$RUN/home" "$RUN/tmp" "$RUN/private" "$EVIDENCE" &&
cat >"$RUN/env" <<EOF &&
CHECKOUT='$CHECKOUT'
EVIDENCE='$EVIDENCE'
PROFILE='$([ "$(uname)" = Darwin ] && echo mac || echo om1)'
export UV_CACHE_DIR='$(uv cache dir)' UV_PYTHON_INSTALL_DIR='$(uv python dir)'
export MISE_CONFIG_DIR='${XDG_CONFIG_HOME:-$HOME/.config}/mise' MISE_DATA_DIR='${XDG_DATA_HOME:-$HOME/.local/share}/mise'
export MISE_STATE_DIR='${XDG_STATE_HOME:-$HOME/.local/state}/mise' MISE_CACHE_DIR='${XDG_CACHE_HOME:-$HOME/.cache}/mise'
export HOME='$RUN/home' TMPDIR='$RUN/tmp' XDG_CONFIG_HOME='$RUN/home/.config' XDG_DATA_HOME='$RUN/home/.local/share'
export XDG_STATE_HOME='$RUN/home/.local/state' XDG_CACHE_HOME='$RUN/home/.cache'
unset CODEX_HOME PI_CODING_AGENT_DIR OPENCODE_CONFIG_DIR
EOF
cat >>"$RUN/env" <<'EOF' &&
record() {
  name=$1
  shift
  printf '%s\n' "$*" >"$EVIDENCE/$name.cmd"
  "$@" >"$EVIDENCE/$name.out" 2>"$EVIDENCE/$name.err"
  status=$?
  echo "$status" >"$EVIDENCE/$name.exit"
  echo "$name: exit $status"
  return "$status"
}
EOF
git -C "$CHECKOUT" rev-parse HEAD >"$EVIDENCE/head.txt" &&
git -C "$CHECKOUT" status --short >"$EVIDENCE/status.txt" &&
echo "RUN=$RUN"
```

`env` keeps uv's cache and Python, and mise's folders, on their real paths. Without them, uv downloads again into the test home and mise's shims refuse to run. It unsets the folder overrides of Codex, Pi, and OpenCode, so each one reads the test home. `record NAME COMMAND...` saves a command with its stdout, stderr, and exit code in the evidence folder.

## Doctor

Run it after Launch, and whenever a result looks wrong. It reads only.

```bash
( . "${RUN:?}/env" && cd "$CHECKOUT" &&
  printf 'checkout %s\nhome     %s\nevidence %s\n' "$CHECKOUT" "$HOME" "$EVIDENCE" &&
  for tool in git just uv codex pi opencode; do command -v "$tool" >/dev/null || echo "missing: $tool"; done &&
  uv --version )
```

The run is worth driving when `home` is `$RUN/home`, no `missing:` line appears, and `uv --version` prints a version. Discovery needs `codex`, `pi`, and `opencode`; without one, its agent reports `unverified`.

## Drive

Read [features/README.md](features/README.md), then run its features in order: [compile](features/compile.md), [install](features/install.md), and [discovery](features/discovery.md). Each assumes the previous one passed in the same run. A run that checks only discovery still installs first, because discovery reads the test home that the install fills.

## Evidence

The evidence folder holds:

- `head.txt` and `status.txt`: the commit and the uncommitted changes the run tested
- `NAME.cmd`, `NAME.out`, `NAME.err`, and `NAME.exit` for each recorded command

[features/README.md](features/README.md) says when a feature passes and how to report one that fails.

## Cleanup

Run this after a pass, a failure, or an interruption:

```bash
if [ "${RUN:?}" != "${RUN#/var/tmp/verify-skills.}" ]; then rm -rf "$RUN"; else echo "refusing to delete $RUN" >&2; fi
```

It deletes the run folder and nothing else. The evidence folder sits outside it and stays. The recipes start no process that outlives its command, so there is nothing to stop.
