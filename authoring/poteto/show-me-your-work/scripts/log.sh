#!/usr/bin/env bash
# Append a well-formed row to a show-me-your-work decision log (TSV).
# Answers in one JSON line (docs/references/script-output.md); see --help.
set -euo pipefail

help() {
	cat <<'EOF'
usage: log.sh <logfile> <phase> <decision> <why> <evidence> <result>

Append one row to a show-me-your-work decision log (TSV), writing the header
first when the file is new. ts is stamped in UTC. Tabs and newlines in a cell
become spaces, and a cell starting with =, +, -, or @ gets a leading quote.

Answers in one JSON line: {"ok":true,"changes":[["append","<absolute logfile>"]]}
on stdout, or {"ok":false,"errors":[...]} as the last line of stderr.

Examples:
  log.sh decisions.tsv harness "took baseline screenshots" "to catch visual drift" baseline/ "120 saved"
  log.sh .audit/migrate.tsv widget "moved the styles" "keep the diff small" "commit 7c21e0a" "pixel-diff 0"

Exit codes: 0 appended, 1 cannot write the log, 2 usage error, 130 interrupted, 143 terminated
EOF
}

# Print $1 as a JSON string, escaping quotes, backslashes, and control characters.
json() {
	local s=$1 out='' c i
	for ((i = 0; i < ${#s}; i++)); do
		c=${s:i:1}
		case $c in
		\" | \\) out+=\\$c ;;
		[[:cntrl:]])
			printf -v c '\\u%04x' "'$c"
			out+=$c
			;;
		*) out+=$c ;;
		esac
	done
	printf '"%s"' "$out"
}

# fail <exit code> <error> [help]: answer as the last line of stderr, then exit.
fail() {
	local help=''
	[ -z "${3-}" ] || help=",\"help\":$(json "$3")"
	printf '{"ok":false,"errors":[%s]%s}\n' "$(json "$2")" "$help" >&2
	exit "$1"
}
trap 'fail 130 interrupted' INT
trap 'fail 143 terminated' TERM
trap 'fail 1 "unexpected failure at line $LINENO of $0"' ERR

case ${1-} in
-h | --help)
	help
	exit 0
	;;
esac
[ "$#" -eq 6 ] || fail 2 "expected 6 arguments, got $#" "$0 --help"

logfile="$1"
shift
case $logfile in
/*) path=$logfile ;;
*) path=$PWD/${logfile#./} ;;
esac
unwritable="cannot write $path; pass a log path you can write to"

logdir="$(dirname -- "$logfile")"
[ -d "$logdir" ] || mkdir -p -- "$logdir" || fail 1 "$unwritable"

if [ ! -f "$logfile" ]; then
	printf 'ts\tphase\tdecision\twhy\tevidence\tresult\n' >"$logfile" || fail 1 "$unwritable"
fi

ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
# Strip tabs/newlines/CR so cells stay on one line, and prefix any cell
# whose first char a spreadsheet would parse as a formula (=, +, -, @)
# with a single quote. The skill expects this log to be read in
# spreadsheets, so attacker-controlled evidence (PR titles, filenames,
# generated text) must not become formula execution when a reviewer
# opens the file.
clean() {
	local v
	v=$(printf '%s' "$1" | tr '\t\n\r' '   ')
	case "$v" in
	=* | +* | -* | @*) printf "'%s" "$v" ;;
	*) printf '%s' "$v" ;;
	esac
}
printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
	"$ts" "$(clean "$1")" "$(clean "$2")" "$(clean "$3")" "$(clean "$4")" "$(clean "$5")" \
	>>"$logfile" || fail 1 "$unwritable"
printf '{"ok":true,"changes":[["append",%s]]}\n' "$(json "$path")"
