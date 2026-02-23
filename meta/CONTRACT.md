# StegDB Canonical Audit Contract

StegDB is the StegVerse Truth Plane (canonical ledger).

SCW is the Command Plane (execution + remediation).

This repository maintains stable canonical artifacts that other repos and workflows link to.

## Required canonical artifacts

- `meta/registry.json`
  - authoritative repo list + canonical flags

- `meta/guardian/guardian_global_latest.json`
- `meta/guardian/GUARDIAN_GLOBAL_LATEST.md`

- `meta/guardian/per_repo/<repo>/guardian_latest.json`
  - (ingested copies) per-repo guardian results

- `meta/aggregated_files.jsonl`
  - aggregated file index across repos (paths + hashes)

- `meta/global_state.json` (or `meta/GLOBAL_STATE.md`)
  - a single pasteable system report

- `meta/attest/manifest.json` (+ checksum)
  - tamper-evident manifest over the above outputs
