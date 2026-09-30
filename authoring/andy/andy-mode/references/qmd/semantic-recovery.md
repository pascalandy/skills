# QMD semantic recovery

Read this reference only when an ordinary QMD search has weak recall, noisy
results, an ambiguous concept, or a question that requires more than one
retrieval step. Every pattern below must be expressed through real QMD commands.

## Diagnose before expanding

Check the failure before adding more queries:

- Wrong corpus: inspect `qmd collection list` and narrow with `-c`
- Known title or phrase missed: use `qmd search` with quoted lexical anchors
- Ambiguous term: add `intent:` and negative lexical terms
- Meaning known but wording unknown: add `vec:`
- Ranking looks wrong: rerun the structured query with `--explain`
- Relevant hit found but context is thin: reopen a line range with
  `qmd get "#docid:from:count"`

Do not compensate for a scope error with a larger candidate set.

## Expansion

Expand the user's language into document language without creating many separate
searches. Prefer one structured query with exact anchors and a semantic
paraphrase:

```bash
qmd query -c docs $'intent: Find the release process, not release notes.\nlex: "release workflow" publish tag changelog -notes\nvec: how the project cuts and publishes a new release'
```

Put the strongest typed search line first because it receives extra fusion
weight. Use `lex:` for names and phrases, then `vec:` for meaning.

## Decomposition

Split a question only when its parts could live in different documents. Search
each part deliberately, reopen the best evidence, then synthesize the retrieved
documents. Do not manually normalize QMD scores across separate result sets.

Example decomposition:

1. Find the canonical policy or procedure
2. Extract its identifier, aliases, and referenced documents
3. Search those identifiers for exceptions or implementation details
4. Reopen the relevant documents before comparing them

## Contextual rewriting

Rewrite pronouns and conversation shorthand into a self-contained query. Carry
forward only context that changes retrieval, such as the project, platform,
version, organization, or excluded meaning.

```text
User follow-up: "How do we implement it here?"
Query intent: Implement SSPM in the named project and environment discussed in
the previous turn
```

Do not copy the whole conversation into `intent:`.

## Diagnostic search

For troubleshooting, cover the observed symptom, likely component, and desired
resolution in one structured query. Add competing causes only when the first
pass is weak.

```bash
qmd query -c notes $'intent: Diagnose repeated VPN disconnects on the user\'s Mac.\nlex: VPN disconnect macOS timeout certificate\nvec: why a VPN connection drops every few minutes on macOS'
```

Ask one clarifying question only when its answer would materially change the
collection or query. Otherwise search the two plausible interpretations and
compare reopened evidence.

## HyDE

Use `hyde:` when the user lacks domain vocabulary or short questions remain far
from long explanatory documents. Write a short hypothetical passage that
resembles the document sought, not a confident answer to the user.

```bash
qmd query -c docs $'intent: Find the documented cause of connection pool exhaustion.\nlex: "connection pool" timeout exhaustion\nvec: why database connections time out under concurrency\nhyde: The document explains that every connection is occupied by long-running requests, so new requests wait until the pool timeout expires.'
```

HyDE is a recall tool. Treat the retrieved document, never the hypothetical
passage, as evidence.

## Temporal retrieval

QMD has no general `date`, `status`, `doc_type`, or `sort` filter. Express time
through supported signals:

- restrict to a collection or path that encodes lifecycle state
- search exact years, versions, quarter names, or terms such as `current`,
  `archived`, and `deprecated`
- reopen the document and verify its date or status in the source text

Do not invent metadata filters or infer that the newest search hit is current.

## Multi-hop retrieval

Use a retrieved document to form the next QMD query when the answer depends on
relationships between documents:

1. Find and reopen the primary document
2. Extract exact identifiers, filenames, aliases, or referenced terms
3. Search those anchors with `qmd search`
4. Use a structured query only if the exact hop is insufficient
5. Reopen every document used in the final answer

## Stop condition

Stop expanding when reopened documents directly support the answer. If distinct
exact and semantic passes both fail, report the collections and query forms tried
and say that QMD did not return sufficient evidence.
