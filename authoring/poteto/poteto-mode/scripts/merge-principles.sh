#!/usr/bin/env bash
# Preview principle merges from a local working tree and two offline upstream refs
set -Eeuo pipefail

readonly SCRIPT_NAME="${0##*/}"
TMP_DIR=""
OUTPUT=""
REPORT_COMPLETE=0
VERBOSE=0
DEBUG="${MERGE_PRINCIPLES_DEBUG:-0}"
POSITIONAL_ARGS=()

fct_answer() {
	local code="$1" message="${2:-}"
	if [[ "$code" -eq 0 ]]; then
		jq -nc --arg file "$OUTPUT" '{ok:true,file:$file}'
	elif [[ "$code" -eq 2 ]]; then
		jq -nc --arg error "$message" --arg help "$SCRIPT_NAME --help" \
			'{ok:false,errors:[$error],help:$help}' >&2
	else
		local report=""
		[[ "$REPORT_COMPLETE" -eq 0 ]] || report="$OUTPUT"
		jq -nc --arg error "$message" --arg file "$report" \
			'{ok:false,errors:[$error]} + if $file == "" then {} else {file:$file} end' >&2
	fi
}

fct_die() {
	fct_answer "${2:-1}" "$1"
	trap - ERR
	exit "${2:-1}"
}

fct_cleanup() {
	[[ -z "$TMP_DIR" ]] || rm -rf -- "$TMP_DIR"
	return 0
}

fct_on_error() {
	trap - ERR
	[[ "$DEBUG" != 1 ]] || printf 'Failed at line %s: %s\n' "$1" "$2" >&2
	fct_die "Preview failed; rerun the same command with --debug, then check paths, Git objects and output permissions"
}

fct_on_signal() {
	trap '' INT TERM
	fct_die "Preview interrupted; rerun the same command" "$1"
}

fct_usage() {
	cat <<EOF
Usage: $SCRIPT_NAME [options] [--] <local root> <upstream checkout> <base> <head>

Preview principles from the local WORKING TREE against two upstream Git commits.
Reads authoring/poteto/poteto-mode/principles/*.md and the separate
authoring/poteto/principle-prove-it-works/SKILL.md. Upstream principles live at
pstack/skills/principle-*/SKILL.md. Frontmatter is removed from skill files.
Requires Bash, Git with --no-lazy-fetch support, jq and awk.
No network, version guessing or source writes.

Options:
  -h, --help           Show help, even alongside invalid arguments
  -o, --output FILE    Write the JSON report to a new file (default: temp file)
  -v, --verbose        Print each principle's state on stderr
      --debug          Print failed-command details (also MERGE_PRINCIPLES_DEBUG=1)

The report contains records {path,state,conflict_blocks}, then bodies {path,body}.
States: clean, conflict, new-upstream, local-only. Bodies retain diff3 markers.
Clean means no textual conflict; the body may still remove local text. Compare
every body with its local source before adopting changes, including prior cuts
left out of the sync ledger. This preview does not approve or apply any change.
New-upstream means present at head and absent locally; local-only means present
locally and absent at head. These include deletions on the missing side. Renames
appear as separate local-only and new-upstream records.
The final JSON answer names the completed report under file. On failure stdout
is empty and the last stderr line is {"ok":false,"errors":[...]}.

Exit codes: 0 no conflicts (including new-upstream/local-only), 1 conflicts or
runtime failure, 2 invalid arguments/refs, 130 SIGINT, 143 SIGTERM.

Examples:
  $SCRIPT_NAME /work/skills /work/plugins 71ed0d1 99743e9
  $SCRIPT_NAME -o /tmp/principles.json /work/skills /work/plugins v0.15.0 HEAD
  $SCRIPT_NAME --help
EOF
}

fct_parse_arguments() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		-o | --output)
			[[ $# -gt 1 && -n "$2" ]] || fct_die "Missing output path; run $SCRIPT_NAME --help" 2
			OUTPUT="$2"
			shift 2
			;;
		--output=*)
			OUTPUT="${1#*=}"
			[[ -n "$OUTPUT" ]] || fct_die "Missing output path; run $SCRIPT_NAME --help" 2
			shift
			;;
		-v | --verbose)
			VERBOSE=1
			shift
			;;
		--debug)
			DEBUG=1
			shift
			;;
		--)
			shift
			POSITIONAL_ARGS+=("$@")
			break
			;;
		-*)
			if [[ "$1" =~ ^-v+$ ]]; then
				VERBOSE=1
				shift
			else fct_die "Unknown option $1; run $SCRIPT_NAME --help" 2; fi
			;;
		*)
			POSITIONAL_ARGS+=("$1")
			shift
			;;
		esac
	done
	[[ ${#POSITIONAL_ARGS[@]} -eq 4 ]] || fct_die "Expected local root, upstream checkout, base and head; run $SCRIPT_NAME --help" 2
	[[ "$OUTPUT" != - ]] || fct_die "The report needs a file path; run $SCRIPT_NAME --help" 2
}

fct_git() {
	env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_OBJECT_DIRECTORY -u GIT_COMMON_DIR \
		GIT_OPTIONAL_LOCKS=0 git --no-lazy-fetch "$@"
}

fct_strip_frontmatter() {
	local first
	IFS= read -r first <"$1" || true
	if [[ "$first" == --- ]]; then
		awk 'NR == 1 {next} !body {if ($0 == "---") body=1; next} {print} END {if (!body) exit 1}' "$1"
	else
		cat "$1"
	fi
}

fct_execute_this() {
	local root upstream base head ref name path source state blocks total=0 file output_parent
	root="$(CDPATH='' cd -- "${POSITIONAL_ARGS[0]}" && pwd -P)" || fct_die "Invalid local root ${POSITIONAL_ARGS[0]}; run $SCRIPT_NAME --help" 2
	[[ -d "$root/authoring/poteto/poteto-mode/principles" ]] ||
		fct_die "Local root lacks authoring/poteto/poteto-mode/principles; pass the source repository root to $SCRIPT_NAME" 2
	upstream="${POSITIONAL_ARGS[1]}"
	# Resolve both commits before listing files, merging or creating any report
	base="$(fct_git -C "$upstream" rev-parse --verify --end-of-options "${POSITIONAL_ARGS[2]}^{commit}" 2>/dev/null)" ||
		fct_die "Unknown upstream base ref ${POSITIONAL_ARGS[2]}; supply an existing local commit to $SCRIPT_NAME" 2
	head="$(fct_git -C "$upstream" rev-parse --verify --end-of-options "${POSITIONAL_ARGS[3]}^{commit}" 2>/dev/null)" ||
		fct_die "Unknown upstream head ref ${POSITIONAL_ARGS[3]}; supply an existing local commit to $SCRIPT_NAME" 2
	if [[ -n "$OUTPUT" ]]; then
		output_parent="${OUTPUT%/*}"
		[[ "$OUTPUT" == */* ]] || output_parent=.
		[[ -n "$output_parent" ]] || output_parent=/
		[[ ! -e "$OUTPUT" && ! -L "$OUTPUT" && -d "$output_parent" && -w "$output_parent" ]] ||
			fct_die "Cannot create report $OUTPUT; choose a new writable path with $SCRIPT_NAME --output" 2
	fi
	TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/merge-principles.XXXXXXXX")"
	: >"$TMP_DIR/names"
	: >"$TMP_DIR/records"
	: >"$TMP_DIR/bodies"
	for ref in "$base" "$head"; do
		fct_git -C "$upstream" ls-tree -r --name-only "$ref" -- pstack/skills >"$TMP_DIR/$ref.paths"
		[[ -s "$TMP_DIR/$ref.paths" ]] ||
			fct_die "Upstream ref $ref has no pstack/skills content; pass a local pstack checkout to $SCRIPT_NAME" 2
		sed -n 's@^pstack/skills/principle-\([^/]*\)/SKILL.md$@\1@p' "$TMP_DIR/$ref.paths" >>"$TMP_DIR/names"
	done
	for file in "$root"/authoring/poteto/poteto-mode/principles/*.md; do
		[[ -f "$file" ]] || continue
		name="${file##*/}"
		printf '%s\n' "${name%.md}" >>"$TMP_DIR/names"
	done
	if [[ -f "$root/authoring/poteto/principle-prove-it-works/SKILL.md" ]]; then
		printf '%s\n' prove-it-works >>"$TMP_DIR/names"
	fi
	LC_ALL=C sort -u "$TMP_DIR/names" >"$TMP_DIR/sorted"
	while IFS= read -r name; do
		[[ "$name" =~ ^[a-z0-9][a-z0-9-]*$ ]] || fct_die "Invalid principle name $name; use lowercase letters, digits and hyphens"
		path="authoring/poteto/poteto-mode/principles/$name.md"
		[[ "$name" != prove-it-works ]] || path="authoring/poteto/principle-prove-it-works/SKILL.md"
		source="pstack/skills/principle-$name/SKILL.md"
		blocks=0
		for ref in "$base" "$head"; do
			: >"$TMP_DIR/$ref.body"
			if grep -Fxq "$source" "$TMP_DIR/$ref.paths"; then
				fct_git -C "$upstream" show "$ref:$source" >"$TMP_DIR/raw"
				fct_strip_frontmatter "$TMP_DIR/raw" >"$TMP_DIR/$ref.body"
			fi
		done
		if [[ ! -f "$root/$path" ]]; then
			grep -Fxq "$source" "$TMP_DIR/$head.paths" || continue
			state=new-upstream
			cp "$TMP_DIR/$head.body" "$TMP_DIR/merged"
		elif ! grep -Fxq "$source" "$TMP_DIR/$head.paths"; then
			state=local-only
			fct_strip_frontmatter "$root/$path" >"$TMP_DIR/merged"
		else
			fct_strip_frontmatter "$root/$path" >"$TMP_DIR/local"
			if fct_git merge-file -p --diff3 -L local -L base -L upstream \
				"$TMP_DIR/local" "$TMP_DIR/$base.body" "$TMP_DIR/$head.body" >"$TMP_DIR/merged"; then
				state=clean
			else
				blocks=$?
				[[ "$blocks" -lt 128 ]] || fct_die "Cannot merge $path; check its text and rerun $SCRIPT_NAME --debug"
				state=conflict
				total=$((total + blocks))
			fi
		fi
		jq -nc --arg path "$path" --arg state "$state" --argjson count "$blocks" \
			'{path:$path,state:$state,conflict_blocks:$count}' >>"$TMP_DIR/records"
		jq -nc --arg path "$path" --rawfile body "$TMP_DIR/merged" '{path:$path,body:$body}' >>"$TMP_DIR/bodies"
		[[ "$VERBOSE" -eq 0 ]] || printf '%s: %s (%s blocks)\n' "$path" "$state" "$blocks" >&2
	done <"$TMP_DIR/sorted"
	jq -n --slurpfile records "$TMP_DIR/records" --slurpfile bodies "$TMP_DIR/bodies" \
		'{records:$records,bodies:$bodies}' >"$TMP_DIR/report"
	if [[ -z "$OUTPUT" ]]; then
		OUTPUT="$(mktemp "${TMPDIR:-/tmp}/merge-principles-report.XXXXXXXX")"
		cat "$TMP_DIR/report" >"$OUTPUT"
	else
		(
			set -o noclobber
			cat "$TMP_DIR/report" >"$OUTPUT"
		) ||
			fct_die "Cannot create report $OUTPUT; choose a new writable path with $SCRIPT_NAME --output" 2
	fi
	REPORT_COMPLETE=1
	[[ "$total" -eq 0 ]] || fct_die "$total conflict blocks; inspect $OUTPUT and resolve the preview before any upstream sync"
}

fct_main() {
	local arg
	for arg in "$@"; do
		case "$arg" in
		--) break ;;
		-h | --help)
			fct_usage
			exit 0
			;;
		esac
	done
	trap fct_cleanup EXIT
	trap 'fct_on_error "$LINENO" "$BASH_COMMAND"' ERR
	trap 'fct_on_signal 130' INT
	trap 'fct_on_signal 143' TERM
	if ! command -v jq >/dev/null 2>&1; then
		printf '%s\n' '{"ok":false,"errors":["Missing jq; install it with brew install jq or your system package manager"]}' >&2
		exit 1
	fi
	fct_parse_arguments "$@"
	command -v git >/dev/null 2>&1 || fct_die "Missing Git; install it with brew install git or your system package manager"
	git --no-lazy-fetch --version >/dev/null 2>&1 ||
		fct_die "Git lacks --no-lazy-fetch support; install a Git release supporting that option before running $SCRIPT_NAME"
	fct_execute_this
	fct_answer 0
}

fct_main "$@"
