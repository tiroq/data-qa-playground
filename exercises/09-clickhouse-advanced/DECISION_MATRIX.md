# Session 09 — Design Comparison Worksheet

Use **after** a candidate proposes at least one architecture. This is a template, not a scored answer key.

## Contract to agree first

- Logical record grain:
- Immutable event identity (if defined):
- Version and conflict resolution:
- Query / account aggregate semantics:
- Eligibility cutoff and freshness objective:
- Is raw source history recoverable, and for how long?

## Compare actual proposals

| Proposal | Logical correctness | Replay / tie behavior | Query cost | Storage / operational cost | Failure observability | Migration / rollback |
|---|---|---|---|---|---|---|
| Proposal A (candidate) | | | | | | |
| Proposal B (alternative discussed) | | | | | | |
| Proposal C (only if needed) | | | | | | |

## Candidate's choice

- Selected architecture:
- Why it best fits the stated constraints:
- Strongest counterargument:
- What could fail:
- Minimum proof / regression test:
- Evidence still missing:

## Concrete QA invariants

| Business invariant | Query or observation that can falsify it | Input case / fixture | Expected outcome or open question |
|---|---|---|---|
| Latest state agrees with version contract | | | |
| Duplicate delivery does not inflate logical trade count | | | |
| Unresolved max-version conflict is reported | | | |
| Backfill and live streams do not double-count | | | |
| Retention preserves required audit source | | | |

Do not fill a verdict without a candidate answer or executed evidence.
