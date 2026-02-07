# StegDB Schemas

This folder contains machine-readable schemas used by StegDB to validate inputs and outputs.

These schemas are designed to support:
- repeatable, non-destructive repository reviews
- documentation alignment without gatekeeping
- consistent reporting across many repositories

Nothing in these schemas implies enforcement, authority, or irreversible changes.

---

## Schemas

### `review_schema_v1.yml`
**Purpose:** Validates a StegDB review request file (typically `reviews/<repo>/review.yml`).

A review request declares:
- which repo is being reviewed
- the repo’s intent and lifecycle status
- the scope of review (read-only audit vs. audit + doc suggestions)
- checks to run
- output locations

### `review_result_v1.yml`
**Purpose:** Validates a StegDB review output file (typically `stegdb_review/result.yml`).

A review result contains:
- an overall confidence signal (`green | yellow | red`)
- a rationale summary
- optional inventories and findings
- legacy/deprecation candidates (non-destructive)
- suggested documentation changes
- first-contact issues and recommendations
- failure mode enumeration

---

## Examples

Examples live in `../examples/`:

- `examples/review_request_example.yml`
- `examples/review_result_example.yml`

These can be copied and adapted repo-by-repo.

---

## Design Constraints

- Reviews are **non-destructive** by default.
- Deprecation is **signaling**, not deletion.
- Forking and reinterpretation are expected.
- These schemas provide structure, not authority.
