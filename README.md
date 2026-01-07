# StegDB

StegDB is StegVerse-Labs’ **canonical database + protocol hub** for keeping many repos consistent, auditable, and “self-healing.”

It provides:
- **Canonical templates** (workflows + baseline repo structure)
- **Protocols** (e.g., custody, evidence confidence, notifications, HEE)
- **Schemas** and validation targets
- **Registry + metadata** (what repos exist, what they contain, dependency status)
- **Automation** to sync canonical → repos and produce aggregated status

> Think of StegDB as the place where StegVerse defines “what correct looks like,” then continuously pushes that correctness outward.

---

## Repository Structure (as currently implemented)

### `.github/workflows/`
Operational workflows for syncing and validating:
- `bootstrap-stegdb-dirs.yml` — ensures required StegDB internal dirs exist
- `stegdb-central.yml` — “hub” workflow (entry point for orchestrations)
- `stegdb-ingest-only.yml` — ingestion-only runs (no pushing outward)
- `sync-to-canonical.yml` / `dispatch-sync-to-canonical.yml` — publish/sync actions
- `publish-canonical.yml` — produce canonical outputs
- `full-cycle.yml` — end-to-end run (ingest → evaluate → publish/saybe sync)
- `workflow-lint.yml` — lint workflow files

### `canonical/`
Canonical exports organized by project (example currently present):
- `canonical/cosden/…` (workflows, src structure, Dockerfile, etc.)

### `profiles/base/.github/workflows/`
Reusable baseline workflows intended to be copied into repos:
- `sync-to-canonical.yml`
- `workflow-lint.yml`

### `protocols/`
Shared protocols that other repos can adopt or reference:
- `protocols/custody/`
  - `custody-transition-spec.md`
  - `custody-transition.schema.yml`
- `protocols/hee/`
  - `artifact.schema.yml`
  - `evidence-confidence-policy.md`
- `protocols/notifications/`
  - `custody-notifications.md`

### `schemas/`
JSON schema definitions used for validation:
- `dependency_status.schemas.json`

### `meta/`
Generated/aggregated state:
- `aggregated_files.jsonl`
- `dependency_status.json`

### `registry/`
What repos exist and how StegDB should treat them:
- `repos.json`

### `repos/<RepoName>/`
Per-repo inventories (example):
- `repos/CosDen/files.json`

### `repairs/<RepoName>/`
Plans and outputs produced by repair tooling (example):
- `repairs/CosDen/repair_plan.json`

### `scripts/`
Standalone scripts (example):
- `write_dependency_status.py`

### `tools/`
StegDB automation tooling (examples currently present):
- `register_repo.py`
- `ingest_repo_metadata.py`
- `generate_repo_metadata.py`
- `evaluate_dependencies.py`
- `repair_repos.py`
- `dispatch_repo_event.py`
- `bootstrap_canonical_prs.py`
- `run_full_cycle.py`
- `stamp_workflow_headers.py`
- and related helpers/config JSON

---

## What StegDB is for (in plain terms)

### 1) Canonicalization
- Define “the standard” once in StegDB (workflows, policies, structure).
- Export it into `canonical/<project>/…`.
- Push it outward to participating repos.

### 2) Ingestion + Indexing
- Pull repo metadata and file inventories back into StegDB.
- Produce aggregated files and dependency status into `meta/`.

### 3) Protocol enforcement
- Keep protocols (custody, confidence scoring, notifications, HEE packet rules) in one place.
- Allow incident repos (like HouseHold) to reference/adopt them.

---

## Typical Workflows

### “I changed canonical—push it out”
1. Update canonical sources in StegDB
2. Run: **Publish Canonical**
3. Run: **Sync to Canonical** (or dispatch sync)

### “I added a new repo—register it”
1. Add repo to `registry/repos.json`
2. Run: registration/ingestion tooling (or full-cycle)

### “I want a full health sweep”
Run: **full-cycle.yml** (ingest → evaluate → publish → optional sync)

---

## How this connects to HouseHold + HEE

StegDB is the correct home for **protocol-level artifacts** that should be shared across many incident types:
- HEE packet specification & schemas
- Evidence confidence policy
- Custody transition rules + notification policy

HouseHold (and other real-world incident repos) are where the **case-specific evidence + letters** live.

---

## Status / Philosophy

StegDB is intentionally:
- **mechanical** (repeatable, automatable)
- **auditable** (outputs are written to `meta/` and can be diffed)
- **scalable** (handles 30+ repos by design)

If you want to “force all evidence through an ingestion engine,” StegDB is the right place to define the standard and the validation rules. Individual incident repos can remain lightweight and only implement the minimum required structure.

---

## License / Safety Notes

This repository is meant to store:
- protocols, schemas, public templates, non-sensitive automation logic

Avoid committing:
- credentials, personal identifiers, private receipts, or unredacted documents
unless a dedicated private repo is used.

---
