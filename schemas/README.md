# StegDB Schemas

This folder contains machine-readable schemas used by StegDB to validate inputs and outputs.

These schemas support:
- repeatable, non-destructive repository reviews
- documentation alignment without gatekeeping
- consistent reporting across many repositories

These schemas provide **structure**, not authority.

---

## Schemas

### `review_schema_v1.yml`
Validates a StegDB review request file (typically `reviews/<repo>/review.yml`).

A review request declares:
- which repo is being reviewed
- the repo’s intent and lifecycle status
- review scope (read-only audit vs. audit + doc suggestions)
- checks to run (including minimum standard evaluation)
- output locations

### `review_result_v1.yml`
Validates a StegDB review result file (typically `stegdb_review/result.yml`).

A review result contains:
- an overall confidence signal (`green | yellow | red`)
- a rationale summary
- optional inventories and findings
- legacy/deprecation candidates (non-destructive)
- suggested documentation changes
- first-contact issues and recommendations
- failure mode enumeration
- minimum-standard evaluation (`minimum_standard_v1`)

---

## Minimum Standard

StegVerse defines a lightweight baseline for repo clarity and future-proofing.
StegDB can evaluate repos against this baseline and report gaps without enforcing changes.

Canonical standard doc (recommended path):
- `docs/StegVerse-Repo-Minimum-Standard-v1.md`

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
- Validation prevents silent drift and reduces first-contact failures.
