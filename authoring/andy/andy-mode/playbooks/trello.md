---
description: "Manage Trello boards, lists, and cards through the Trello REST API."
configuration-is-needed: true
api-key: "TRELLO_API_KEY, TRELLO_TOKEN"
---

# Trello Skill

Manage Trello boards, lists, and cards.

## Usage

All commands use curl to hit Trello REST API. Run **Setup**, the resolver and the requested recipe in one shell invocation so their variables remain available. In an interactive terminal, wrap that whole sequence in one subshell `( ... )` so an error exits only the sequence.

Use the read recipes by default. This board is shared: obtain the user's approval for the specific change before running any write recipe below. Keep board data and credentials out of public issues, PRs and logs; publish only aggregate verification counts.

### Validate the API call is working

Run **Setup** first.

```bash
curl --fail --silent --show-error --get 'https://api.trello.com/1/members/me' \
  --data-urlencode "key=$TRELLO_API_KEY" \
  --data-urlencode "token=$TRELLO_TOKEN" | jq
```

### Resolve and validate the default SDC board

`TRELLO_BOARD_SDC` stores a Trello URL, not an API board ID. Run **Setup** first to export `TRELLO_API_KEY` and `TRELLO_TOKEN`, then run this snippet in bash or zsh before any SDC board request. Pass `${board_id}` to `/1/boards/...` endpoints.

```bash
board_url="$(chezmoi secret keyring get --service=TRELLO_BOARD_SDC --user=url)" || exit 1
board_id="$(printf '%s\n' "$board_url" | sed -nE 's#^https://trello\.com/b/([A-Za-z0-9]+)(/[^[:space:]]*)?$#\1#p')"
if [ -z "$board_id" ]; then
  printf '%s\n' 'TRELLO_BOARD_SDC must be a Trello board URL: https://trello.com/b/<board-id>/...' >&2
  exit 1
fi

curl --fail-with-body --silent --show-error --get "https://api.trello.com/1/boards/${board_id}" \
  --data-urlencode "key=$TRELLO_API_KEY" \
  --data-urlencode "token=$TRELLO_TOKEN" \
  --data-urlencode "fields=id,name" | jq -e 'select(.id != null and .name != null) | {id, name}'
```

### List boards

By default, user is working on this board (SDC):

````shell
chezmoi secret keyring get --service=TRELLO_BOARD_SDC --user=url
````

to list them all:

```bash
curl -s "https://api.trello.com/1/members/me/boards?key=$TRELLO_API_KEY&token=$TRELLO_TOKEN" | jq '.[] | {name, id}'
```

### List lists in the default SDC board

Run **Resolve and validate the default SDC board** first.

```bash
curl --fail-with-body --silent --show-error --get "https://api.trello.com/1/boards/${board_id}/lists" \
  --data-urlencode "key=$TRELLO_API_KEY" \
  --data-urlencode "token=$TRELLO_TOKEN" \
  --data-urlencode "fields=name,id" | jq '.[] | {name, id}'
```

### List cards in a list

```bash
curl -s "https://api.trello.com/1/lists/{listId}/cards?key=$TRELLO_API_KEY&token=$TRELLO_TOKEN" | jq '.[] | {name, id, desc}'
```

### Read open cards with list names, last activity and labels

Requires `curl`, `jq` and `chezmoi` (`command -v curl jq chezmoi`). Run **Setup** and the resolver first. Keep the variables below in the same shell for the decision recipe. Each TSV line contains four fields: card name, list name, last activity, labels. `@tsv` escapes embedded tabs and newlines so one card occupies one line.

```bash
set -o pipefail
lists_json="$(curl --fail --silent --show-error --get "https://api.trello.com/1/boards/${board_id}/lists" \
  --data-urlencode "key=$TRELLO_API_KEY" \
  --data-urlencode "token=$TRELLO_TOKEN" \
  --data-urlencode "filter=all" \
  --data-urlencode "fields=id,name")" || exit 1
open_cards="$(curl --fail --silent --show-error --get "https://api.trello.com/1/boards/${board_id}/cards/open" \
  --data-urlencode "key=$TRELLO_API_KEY" \
  --data-urlencode "token=$TRELLO_TOKEN" \
  --data-urlencode "fields=name,idList,dateLastActivity,labels,shortLink,desc")" || exit 1
printf '%s\n' "$lists_json" "$open_cards" | jq -r -s '
  (.[0] | map({key: .id, value: .name}) | from_entries) as $names
  | .[1][] | [.name, ($names[.idList] // error("Unknown list")),
      .dateLastActivity, ([.labels[] | .name] | join(", "))] | @tsv'
```

### Read comments and card activity since a date

Run **Setup** and the resolver first. Set `since` to the requested ISO 8601 date. The helper reads `boards/{id}/actions?filter=commentCard&since=<date>` or the activity filter below. It pages with `before` until no actions remain, so a busy board is not silently truncated at the API's 1,000-action limit. See the [Trello API paging guide](https://developer.atlassian.com/cloud/trello/guides/rest-api/api-introduction/#paging).

```bash
set -o pipefail
since='2026-10-01T00:00:00Z' # Replace with the requested start date
fct_trello_actions() {
  local action_filter="$1" before='' page
  while :; do
    page="$(curl --fail --silent --show-error --get "https://api.trello.com/1/boards/${board_id}/actions" \
      --data-urlencode "key=$TRELLO_API_KEY" \
      --data-urlencode "token=$TRELLO_TOKEN" \
      --data-urlencode "filter=$action_filter" \
      --data-urlencode "since=$since" \
      --data-urlencode "before=$before" \
      --data-urlencode "limit=1000")" || return 1
    [ "$(printf '%s\n' "$page" | jq 'length')" -gt 0 ] || break
    printf '%s\n' "$page" | jq -c '.[]' || return 1
    before="$(printf '%s\n' "$page" | jq -r 'last.id')" || return 1
  done
}
comments_json="$(fct_trello_actions commentCard | jq -s '.')" || exit 1
printf '%s\n' "$comments_json" | jq -r '.[] |
  [.date, .data.card.name, .data.text,
   ("https://trello.com/c/" + .data.card.shortLink)] | @tsv'

fct_trello_actions 'updateCard:idList,updateCard:closed,createCard' | jq -r '
  [.date, .type, .data.card.name, (.data.listBefore.name // ""),
   (.data.listAfter.name // .data.list.name // ""), (if .data.card | has("closed") then .data.card.closed | tostring else "" end),
   ("https://trello.com/c/" + .data.card.shortLink)] | @tsv'
```

### Find decisions waiting for an answer

In one shell invocation, run **Setup** and the resolver. From the read recipes above, prepare `lists_json` and `open_cards`, set `since`, define `fct_trello_actions`, and assign `comments_json`. Skip the TSV print commands and the separate activity query when only decisions are requested.

`Besoin de décision` is the decision label; `décision requise` is the text convention in a card's name, description or comments. The query finds open cards with either marker and prints their name, last activity and clickable `https://trello.com/c/<shortLink>` link. Inspect those cards' comments before stating which decisions remain unanswered: a marker alone does not prove that a decision is still pending, and `comments_json` covers only the chosen date window. Widen `since` when necessary.

```bash
[ -n "${open_cards:-}" ] && [ -n "${comments_json:-}" ] || { printf '%s\n' 'Run the open-card and comment recipes in this same shell first' >&2; exit 1; }
printf '%s\n' "$comments_json" "$open_cards" | jq -r -s '
  [.[0][] | select(.data.text | test("décision requise"; "i"))
    | .data.card.id] as $comment_ids
  | .[1][] | select(
      any(.labels[]; .name == "Besoin de décision")
      or ([.name, .desc] | join(" ") | test("décision requise"; "i"))
      or (.id as $id | $comment_ids | index($id)))
  | [.name, .dateLastActivity, ("https://trello.com/c/" + .shortLink)] | @tsv'
```

### Create a card from an available SDC ID

For SDC cards, use a pre-created placeholder in the **`Nouveaux points`** list. A placeholder has the exact name `SDC_<number>` (for example, `SDC_205`). Its number is the card ID.

1. Find the `Nouveaux points` list and select the available placeholder with the smallest number. The order displayed by Trello does not determine the next ID.
2. Rename that placeholder to `SDC_<number> <Card Title>` and set its description. This consumes the placeholder; do not create a second card with `POST`.
3. If no placeholder matches `^SDC_[0-9]+$`, stop and ask the user to create new ID placeholders. Never invent an ID or reuse an occupied one.

```bash
# Run "Resolve and validate the default SDC board" first.
list_id="$(curl --fail-with-body --silent --show-error --get "https://api.trello.com/1/boards/${board_id}/lists" \
  --data-urlencode "key=$TRELLO_API_KEY" \
  --data-urlencode "token=$TRELLO_TOKEN" \
  --data-urlencode "fields=name,id" | \
  jq -r '.[] | select(.name == "Nouveaux points") | .id')"

# Pick the smallest available placeholder; the result is: Trello card ID<TAB>SDC ID.
slot="$(curl --fail-with-body --silent --show-error --get "https://api.trello.com/1/lists/${list_id}/cards" \
  --data-urlencode "key=$TRELLO_API_KEY" \
  --data-urlencode "token=$TRELLO_TOKEN" \
  --data-urlencode "fields=name,id" | \
  jq -r '[.[]
    | select(.name | test("^SDC_[0-9]+$"))
    | {id, name, number: (.name | capture("^SDC_(?<n>[0-9]+)$").n | tonumber)}
  ] | sort_by(.number) | first // empty | [.id, .name] | @tsv')"

if [[ -z "$slot" ]]; then
  echo "No SDC ID is available in Nouveaux points. Please create new ID placeholders before creating this card." >&2
  exit 1
fi

IFS=$'\t' read -r card_id next_id <<< "$slot"
printf 'Using %s\n' "$next_id"

curl --fail-with-body --silent --show-error -X PUT "https://api.trello.com/1/cards/${card_id}" \
  --data-urlencode "key=$TRELLO_API_KEY" \
  --data-urlencode "token=$TRELLO_TOKEN" \
  --data-urlencode "name=${next_id} Card Title" \
  --data-urlencode "desc=Card description"
```

### Move a card to another list

```bash
curl -s -X PUT "https://api.trello.com/1/cards/{cardId}?key=$TRELLO_API_KEY&token=$TRELLO_TOKEN" \
  -d "idList={newListId}"
```

### Add a comment to a card

```bash
curl -s -X POST "https://api.trello.com/1/cards/{cardId}/actions/comments?key=$TRELLO_API_KEY&token=$TRELLO_TOKEN" \
  -d "text=Your comment here"
```

### Archive a card

```bash
curl -s -X PUT "https://api.trello.com/1/cards/{cardId}?key=$TRELLO_API_KEY&token=$TRELLO_TOKEN" \
  -d "closed=true"
```

## Notes

- Board/List/Card IDs can be found in Trello URL or via list commands. `TRELLO_BOARD_SDC` is a URL; extract and validate `${board_id}` before using a `/1/boards/...` endpoint.
- For SDC card creation, IDs are reserved as placeholders in `Nouveaux points`. Use the smallest placeholder named exactly `SDC_<number>`; a missing number is not available unless its placeholder exists.
- API key and token provide full access to your Trello account - keep them secret!
- Rate limits: 300 requests per 10 seconds per API key; 100 requests per 10 seconds per token; `/1/members` endpoints are limited to 100 requests per 900 seconds

## Examples

```bash
# Get all boards
curl -s "https://api.trello.com/1/members/me/boards?key=$TRELLO_API_KEY&token=$TRELLO_TOKEN&fields=name,id" | jq

# Find a specific board by name
curl -s "https://api.trello.com/1/members/me/boards?key=$TRELLO_API_KEY&token=$TRELLO_TOKEN" | jq '.[] | select(.name | contains("Work"))'

# Get all cards on the default SDC board (run the resolver first)
curl --fail-with-body --silent --show-error --get "https://api.trello.com/1/boards/${board_id}/cards" \
  --data-urlencode "key=$TRELLO_API_KEY" \
  --data-urlencode "token=$TRELLO_TOKEN" \
  --data-urlencode "fields=name,idList" | jq '.[] | {name, list: .idList}'
```

## Setup

Here's instructions if it's not already done.

1. Get your API key: https://trello.com/app-key
2. Generate token (click "Token" link on that page)
3. With `chezmoi` installed and the keyring entries configured, export and validate the environment variables before running any recipe:

```bash
TRELLO_API_KEY="$(chezmoi secret keyring get --service=TRELLO_API_KEY --user=api_key)" || exit 1
TRELLO_TOKEN="$(chezmoi secret keyring get --service=TRELLO_TOKEN --user=api_key)" || exit 1
[ -n "$TRELLO_API_KEY" ] && [ -n "$TRELLO_TOKEN" ] || { printf '%s\n' 'Trello credentials are missing' >&2; exit 1; }
export TRELLO_API_KEY TRELLO_TOKEN
```
