---
name: "verify-skills"
description: "Use when verifying `just compile-skills`, `just remote-skills`, `just install-skills`, or `just skills-discover` in the skills repository, such as after changing their scripts or adding, renaming, or moving a skill."
kind: "dev"
---

# Verify skills

Drive the skills repository's real `just` recipes with a test home. The live agent folders stay untouched.

## Launch

Run from inside the checkout under test. The block creates a run folder under `/var/tmp`, writes `$RUN/env`, and prints `RUN`. Later blocks load that file in a subshell. If your shell does not keep variables between commands, set `RUN` to the printed path before each block.

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

`env` keeps uv's cache and Python installation, and mise's folders, on their real paths. This avoids fresh uv downloads and broken mise shims. It unsets the folder overrides of Codex, Pi, and OpenCode, so each reads the test home.

## Doctor

Run it after Launch, and whenever a result looks wrong. It reads only.

```bash
( . "${RUN:?}/env" && cd "$CHECKOUT" &&
  printf 'checkout %s\nhome     %s\nevidence %s\n' "$CHECKOUT" "$HOME" "$EVIDENCE" &&
  for tool in git just uv rsync codex pi opencode; do command -v "$tool" >/dev/null || echo "missing: $tool"; done &&
  uv --version )
```

Proceed when `home` is `$RUN/home`, no `missing:` line appears, and `uv --version` prints a version.

## Drive

Read [features/README.md](features/README.md), then run [compile](features/compile.md), [install](features/install.md), and [discovery](features/discovery.md) in order. Each requires the previous feature to pass in the same run.

## Evidence

`record NAME COMMAND...` saves its command, stdout, stderr, and exit code in `$EVIDENCE`. That folder holds:

- `head.txt` and `status.txt`: the commit and the uncommitted changes the run tested
- `NAME.cmd`, `NAME.out`, `NAME.err`, and `NAME.exit` for each recorded command

## Cleanup

Run this after a pass, a failure, or an interruption:

```bash
if [ "${RUN:?}" != "${RUN#/var/tmp/verify-skills.}" ]; then rm -rf "$RUN"; else echo "refusing to delete $RUN" >&2; fi
```

It deletes the run folder and nothing else. The evidence folder sits outside it and stays. The recipes start no process that outlives its command, so there is nothing to stop.
