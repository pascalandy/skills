# Wiki Map structural maintenance

Use this branch only for `StructureGovernance` on a detected Wiki Map boundary. Load the active `wiki-map` skill and its `references/SCHEMA.md` as the authority for indexes, metadata, ownership, and links. Keep this bounded maintenance workflow; loading the schema does not request a full sweep or migration.

1. Start from the owning index and identify its declared schema and wiki type. At a collection, inspect the relevant child wiki before judging page placement.
2. Compare the requested files and directly affected index or links against that schema. Leave unrelated collections and pages outside the cleanup scope.
3. Plan repairs using the existing documentation's canonical ownership. Preserve source metadata, user-authored content, and established creation dates.
4. Apply and verify only the repairs authorized by the cleanup request. Track all affected pages cumulatively and respect the approval gates defined by Wiki Map.
5. Report each checked boundary, repairs, unresolved findings, and any migration that needs separate authorization. If the schema is legacy, unstamped, or ambiguous, do not silently upgrade it or normalize its topology.

Wiki Map owns schema rules and migration gates. This skill owns the cleanup objective and bounded changes; do not duplicate the schema here. If the schema reference is unavailable, report Wiki Map validation as blocked rather than using generic documentation rules as a substitute.
