"""A stand-in for `gh` that answers the replay's read-only queries from canned facts."""

import json
import os
import re
import sys

REPOS = {
    "widget": ("example-owner/widget", "PUBLIC"),
    "secret-thing": ("example-owner/secret-thing", "PRIVATE"),
}
REPOS.update({full: (full, vis) for full, vis in list(REPOS.values())})


def issue(title, closed=None, parent=None, subs=(), labels=()):
    return {
        "title": title,
        "closedAt": closed,
        "labels": {"nodes": [{"name": x} for x in labels]},
        "parent": {"number": parent[1], "repository": {"nameWithOwner": parent[0]}}
        if parent
        else None,
        "subIssues": {
            "totalCount": len(subs),
            "nodes": [
                {"number": n, "createdAt": at, "repository": {"nameWithOwner": r}}
                for r, n, at in subs
            ],
        },
    }


W, S = "example-owner/widget", "example-owner/secret-thing"
ISSUES = {
    (W, 9): issue(
        "Epic 3 PLANTED FREE TEXT",
        labels=["4-epic"],
        subs=[(W, 10, "2025-12-31T00:00:00Z"), (W, 11, "2025-12-31T00:00:00Z")],
    ),
    (W, 10): issue("Story PLANTED FREE TEXT", parent=(W, 9)),
    (W, 11): issue("Another story", parent=(W, 9)),
    (S, 4): issue("Epic 7 secret-thing PLANTED FREE TEXT", labels=["4-epic"]),
}
PRS = {
    (W, 21): {
        "number": 21,
        "createdAt": "2026-01-01T00:01:00Z",
        "mergedAt": None,
        "closedAt": None,
        "body": "Closes #11.",
        "closingIssuesReferences": {
            "nodes": [{"number": 11, "repository": {"nameWithOwner": W}}]
        },
    },
    (W, 20): {
        "number": 20,
        "createdAt": "2026-01-01T00:01:00Z",
        "mergedAt": "2026-01-01T00:02:00Z",
        "closedAt": "2026-01-01T00:02:00Z",
        "body": "Closes #10. PLANTED FREE TEXT /home/example/path",
        "closingIssuesReferences": {
            "nodes": [{"number": 10, "repository": {"nameWithOwner": W}}]
        },
    },
}
for pr in PRS.values():
    pr["userContentEdits"] = {
        "nodes": [{"editedAt": pr["createdAt"], "diff": pr["body"], "deletedAt": None}],
        "pageInfo": {"hasNextPage": False, "endCursor": None},
    }
PRS[(W, 20)]["userContentEdits"]["nodes"] = [
    {
        "editedAt": "2026-01-01T00:01:01Z",
        "diff": PRS[(W, 20)]["body"],
        "deletedAt": None,
    },
    {
        "editedAt": PRS[(W, 20)]["createdAt"],
        "diff": "Closes #10. Refs example-owner/secret-thing#4",
        "deletedAt": None,
    },
]

args = sys.argv[1:]
if os.environ.get("FAKE_GH_DOWN") and os.path.exists(os.environ["FAKE_GH_DOWN"]):
    print("HTTP 502: Bad Gateway (https://api.github.com/graphql)", file=sys.stderr)
    raise SystemExit(1)
if args[:2] == ["repo", "view"]:
    if args[2] not in REPOS:
        print(
            f"GraphQL: Could not resolve to a Repository with the name '{args[2]}'.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    full, visibility = REPOS[args[2]]
    print(json.dumps({"nameWithOwner": full, "visibility": visibility}))
elif args[:2] == ["api", "graphql"]:
    query = args[3].removeprefix("query=")
    m = re.search(r'repository\(owner:"([^"]+)",name:"([^"]+)"\)', query)
    assert m, query
    repo = f"{m.group(1)}/{m.group(2)}"
    data, missing = {}, False
    # each field answers under its alias, such as `p20: pullRequest(number:20)`, or its name
    for alias, field, n in re.findall(
        r"(?:(\w+): )?(pullRequest|issueOrPullRequest|issue)\(number:(\d+)\)", query
    ):
        ref, name = (repo, int(n)), alias or field
        if field == "pullRequest":
            data[name] = PRS[ref]
        elif field == "issue":
            data[name] = ISSUES.get(ref)
            missing = missing or data[name] is None
        else:
            pr = PRS.get(ref)
            data[name] = (
                {
                    "__typename": "PullRequest",
                    "mergedAt": pr["mergedAt"],
                    "closedAt": pr["closedAt"],
                }
                if pr
                else None
            )
    body: dict[str, object] = {"data": {"repository": data}}
    if missing:
        body["errors"] = [
            {"type": "NOT_FOUND", "message": "Could not resolve to an Issue"}
        ]
    print(json.dumps(body))
    raise SystemExit(1 if missing else 0)
else:
    print(f"fake gh: unexpected arguments {args}", file=sys.stderr)
    raise SystemExit(1)
