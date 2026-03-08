# StegTV Execution Ledger Spec

## Purpose

This protocol defines the canonical StegDB representation for StegTV / TVC
execution-authority events.

The goal is not merely to record token issuance, but to preserve the minimal
forensic chain required to answer:

- who (or what workload) requested authority
- under what policy or bundle context
- for which repo / ref / sha / scope / environment
- whether authority was granted, denied, deferred, or later used

This protocol is canonical and append-oriented.

---

## Canonical object

Schema:

- `schemas/stegtv_execution_event.schema.json`

Schema identity:

- `schema_name: stegtv_execution_event`
- `schema_version: 1.0.0`

---

## Event classes

The canonical event classes are:

- `oidc_exchange`
- `token_issued`
- `token_verified`
- `action_attempted`
- `action_succeeded`
- `action_denied`

Implementations may emit only a subset initially.
For v0.1, the minimum recommended set is:

- `oidc_exchange`
- `token_issued`

---

## Required fields

Each event must include:

- `event_id`
- `time`
- `event_type`
- `decision`
- `issuer`
- `repo`
- `ref`
- `sha`
- `scope`
- `environment`
- `request_id`

These are the minimum fields required to reconstruct execution-authority flow.

---

## Design constraints

### 1. Append-oriented
StegDB stores execution ledger entries as append-only canonical records.

### 2. No secret material
The ledger must never store:
- JWT signing secrets
- raw bearer tokens
- GitHub OIDC raw JWTs
- payment credentials
- plaintext admin credentials

### 3. Safe metadata only
The `meta` object may include:
- run ids
- workflow names
- GitHub claims that are not secret
- validation result summaries
- failure reasons

It must not include secret tokens.

### 4. Canon over cache
Redis or in-memory state may be used for fast revocation / runtime state, but
StegDB is the canonical long-horizon audit memory.

---

## Recommended storage paths in StegDB

- `canon/stegtv/execution_events.jsonl`
- `meta/stegtv/latest_ingest_summary.json`

If these paths do not exist yet, the ingest tool should create them.

---

## Minimum ingest expectations

The StegDB ingest tool should:

1. validate each event against the schema
2. normalize schema identity
3. append valid events to canonical JSONL
4. write an ingest summary to meta

Invalid events should fail the workflow.

---

## Relationship to TVC database migrations

This protocol is the canonical representation layer.

Executable DB migrations for runtime infrastructure belong in the TVC repo.

A canonical SQL reference copy may be stored under:

- `protocols/stegtv/db/`

But StegDB should not treat SQL migrations as validation schemas.

---

## Versioning

Any breaking change to required fields or semantics requires a major schema
version increment.
