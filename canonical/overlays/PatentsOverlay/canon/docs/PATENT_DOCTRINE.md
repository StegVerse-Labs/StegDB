# StegVerse Patents Doctrine (Canonical)

## Purpose
The Patents system exists to:
- identify potentially patentable StegVerse processes
- generate **invention disclosure stubs** and **draft skeletons**
- track deadlines and portfolio metadata
- keep everything auditable and reviewable

## Safety rules (non-negotiable)
- No automatic filing with USPTO or any jurisdiction
- No publication outside the Patents repo
- All outputs are drafts for human/legal review
- Use allowlists for repos, branches, and file paths
- Never ingest secrets or personal data into drafts

## Candidate triggers (v1 baseline)
A change is “patent-candidate” only if at least one is true:
- commit message contains `[PATENT]`
- a file is added/changed under `patent_candidates/**`
- a PR has label `patent-candidate`

## Draft outputs (v1)
- `/disclosures/<id>/disclosure.md`
- `/provisionals/<id>/provisional.md`
- `/provisionals/<id>/claims.md`
- `/provisionals/<id>/diagram.md` (optional)

## Required metadata
- stable candidate id
- source repo + commit SHA
- summary + novelty bullets
- known prior art / related work (if any)
- claim tiers: broad → narrow
- deadlines: provisional → non-provisional

## Canonical manifests
- `allowlist.yaml` format is defined canonically
- `patent_manifest.json` must remain machine-readable
