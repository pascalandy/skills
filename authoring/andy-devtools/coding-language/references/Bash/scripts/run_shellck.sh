#!/usr/bin/env bash
# Lint shell scripts with shellcheck. Answers in one JSON line: {"ok":true} on
# stdout, or {"ok":false,"errors":[...]} as the last line of stderr, after the
# linter's own diagnostics.
set -euo pipefail

usage() {
	cat <<'EOF'
usage: run_shellck.sh [path ...]

Lint each shell script under the given files and folders, or under scripts/ when
none is given. A file counts as a shell script by its extension (.sh, .bash,
.zsh, .command) or its shebang.

Answers {"ok":true} on stdout, or {"ok":false,"errors":[...]} as the last line of
stderr, after shellcheck's diagnostics.

Exit codes: 0 clean or nothing to lint; 1 shellcheck found problems or is
missing; 2 usage error
EOF
}

# Print $1 as a JSON string; quotes, backslashes, and control characters escaped
json() {
	local text=$1 out='' char i
	for ((i = 0; i < ${#text}; i++)); do
		char=${text:i:1}
		case $char in
		\" | \\) out+=\\$char ;;
		[[:cntrl:]])
			printf -v char '\\u%04x' "'$char"
			out+=$char
			;;
		*) out+=$char ;;
		esac
	done
	printf '"%s"' "$out"
}

# fail <exit code> <error> [help]: answer as the last line of stderr, then exit
fail() {
	local help=''
	[[ -z "${3-}" ]] || help=",\"help\":$(json "$3")"
	printf '{"ok":false,"errors":[%s]%s}\n' "$(json "$2")" "$help" >&2
	exit "$1"
}
trap 'fail 130 interrupted' INT
trap 'fail 143 terminated' TERM

is_shell_file() {
	local path="$1"
	case "$path" in
	*.sh | *.bash | *.zsh | *.command)
		return 0
		;;
	esac
	if [[ -f "$path" ]]; then
		local first
		first="$(head -n 1 "$path" 2>/dev/null || true)"
		if [[ "$first" =~ ^#!.*\b(sh|bash|zsh)\b ]]; then
			return 0
		fi
	fi
	return 1
}

add_targets_from_dir() {
	local dir="$1"
	while IFS= read -r -d '' f; do
		if is_shell_file "$f"; then
			TARGETS+=("$f")
		fi
	done < <(find "$dir" -type f -print0)
}

add_target() {
	local path="$1"
	if [[ -d "$path" ]]; then
		add_targets_from_dir "$path"
		return
	fi
	if [[ -f "$path" ]]; then
		if is_shell_file "$path"; then
			TARGETS+=("$path")
		fi
		return
	fi
	fail 2 "path not found: $path" "run_shellck.sh --help"
}

case ${1-} in
-h | --help)
	usage
	exit 0
	;;
esac

command -v shellcheck >/dev/null 2>&1 ||
	fail 1 "shellcheck not found; install it with brew install shellcheck, then rerun"

TARGETS=()
if [[ $# -gt 0 ]]; then
	for arg in "$@"; do
		add_target "$arg"
	done
elif [[ -d "scripts" ]]; then
	add_targets_from_dir "scripts"
else
	fail 2 "no path given and scripts/ not found; pass the files or folders to lint" "run_shellck.sh --help"
fi

if [[ ${#TARGETS[@]} -gt 0 ]] && ! shellcheck -x "${TARGETS[@]}" >&2; then
	fail 1 "shellcheck found problems in ${#TARGETS[@]} file(s) checked; fix what it reports above, then rerun"
fi
printf '{"ok":true}\n'
