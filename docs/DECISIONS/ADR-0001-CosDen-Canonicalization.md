# ADR-0001: Canonicalize CosDen Into StegDB (Retire Submodule)

**Status:** Accepted ✅  
**Date:** 2026-02-07  
**Decision owners:** StegVerse-Labs (public)

## Context

CosDen began as an independent repository and at one point was referenced by StegDB via a Git submodule entry named `CosDen`. Over time, CosDen’s relevant canonical content (e.g., CosDenOS reference material) moved into StegDB canonical space for durability, reviewability, and consistent ingestion.

The submodule pointer remained and later produced CI warnings due to missing `.gitmodules` URL metadata (Git exit code 128 in cleanup steps).

## Decision

1. Maintain CosDen canonical content inside StegDB under:
   - `StegDB/canonical/cosden/...`

2. Retire the stale `CosDen` Git submodule pointer from StegDB.

3. Treat submodules as **exception-only** mechanisms in StegVerse:
   - allowed only when they are explicitly documented and maintained,
   - otherwise prefer canonical ingestion/mirroring.

## Rationale

- Submodules are fragile across time, forks, automation environments, and repo reorganizations.
- Canonical ingestion makes content:
  - readable by default,
  - inspectable without special git operations,
  - more resilient to drift.

## Consequences

### Positive
- Fewer CI warnings and less “false yellow” reliability signaling.
- Lower risk of brittle coupling to historical repo layout.
- Clearer ownership and review flow for canonical artifacts.

### Negative / Tradeoffs
- Canonical copies require explicit update processes if the source repo also continues to evolve.
- Some “single source of truth” purity is traded for operational resilience.

## Notes

This note is public by design. The purpose is to preserve intent and reduce repeated failure modes for future contributors.
