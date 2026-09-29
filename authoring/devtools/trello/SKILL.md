---
name: "trello"
description: "Explicitly triggered when the user mentions `trello`."
homepage: "https://developer.atlassian.com/cloud/trello/rest/"
---

# Trello Skill

Manage Trello boards, lists, and cards.

## Usage

All commands use curl to hit Trello REST API.

### Validate the API call is working

````bash
export TRELLO_API_KEY="$(chezmoi secret keyring get --service=TRELLO_API_KEY --user=api_key)" && export TRELLO_TOKEN="$(chezmoi secret keyring get --service=TRELLO_TOKEN --user=api_key)" && curl -s "https://api.trello.com/1/members/me?key=$TRELLO_API_KEY&token=$TRELLO_TOKEN" | jq
````

### Resolve and validate the default SDC board

`TRELLO_BOARD_SDC` stores a Trello URL, not an API board ID. Run this Bash snippet before any SDC board request. Pass `${board_id}`—never `${board_url}`—to `/1/boards/...` endpoints.

```bash
board_url="$(chezmoi secret keyring get --service=TRELLO_BOARD_SDC --user=url)"
if [[ ! "$board_url" =~ ^https://trello\.com/b/([A-Za-z0-9]+)(/|$) ]]; then
  printf '%s\n' 'TRELLO_BOARD_SDC must be a Trello board URL: https://trello.com/b/<board-id>/...' >&2
  exit 1
fi
board_id="${BASH_REMATCH[1]}"

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
3. Set env vars:

```bash
export TRELLO_API_KEY="$(chezmoi secret keyring get --service=TRELLO_API_KEY --user=api_key)"
export TRELLO_TOKEN="$(chezmoi secret keyring get --service=TRELLO_TOKEN --user=api_key)"
```
