# StegScholar Doctrine (Canonical)

## Purpose
StegScholar is the scholarly research repository for StegVerse:
- peer-review papers
- submission history and outcomes
- figures/diagrams
- reading lists and prior work
- stable primitives and terminology

## Design principles
- Papers are standalone and composable
- No paper depends on StegVerse “as a platform”
- StegVerse serves only as an existence proof
- Terminology is stable, versioned, reusable
- Corrections and errata are append-only

## Repository boundaries
- `papers/**` holds paper content and models
- `submissions/**` holds venue tracking and checklists
- `references/**` holds BibTeX and citations
- `canon/**` holds canonical doctrine and templates

## Publication posture
- Avoid claims that require privileged access
- Separate observation, inference, and normative claims
- Provide falsifiability criteria where possible
