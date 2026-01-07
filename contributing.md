# Contributing to StegDB

StegDB is the canonical standards and protocol repository for StegVerse-Labs.
Contributions should prioritize **stability, auditability, and repeatability** over novelty.

This is not an experimentation sandbox — it is the place where standards are finalized.

---

## Guiding Principles

1. **Canonical first**
   - If a rule, structure, or workflow applies to more than one repo, it belongs here.
2. **Protocols before code**
   - Prefer documented specs and schemas before implementation.
3. **Determinism**
   - StegDB outputs must be reproducible and diff-friendly.
4. **Non-destructive**
   - Never overwrite incident data in downstream repos.

---

## What Belongs in StegDB

### ✅ Appropriate
- Protocol specifications (custody, HEE, evidence confidence, notifications)
- Canonical workflows
- Validation schemas
- Repo registry metadata
- Automation tooling that enforces standards

### ❌ Not Appropriate
- Case-specific evidence
- Personal data
- Letters, claims, or disputes
- Private artifacts (receipts, photos, communications)

Those belong in incident repos (e.g., HouseHold).

---

## Adding or Modifying Protocols

1. Create or update files under:
   - `protocols/<domain>/`
2. If structured data is involved:
   - Add or update schema under `schemas/`
3. Update documentation **before** tooling.
4. If adoption is expected:
   - Reference the protocol in `meta/` or `registry/` if applicable.

---

## Canonical Workflow Changes

When modifying workflows:
- Update both:
  - `.github/workflows/`
  - `profiles/base/.github/workflows/` (if reusable)
- Run `workflow-lint.yml` before merging.

---

## Adding a New Canonical Export

1. Create directory under `canonical/<project>/`
2. Include:
   - workflows
   - structural expectations
   - minimal README explaining intent
3. Ensure it can be synced without assumptions about repo state.

---

## Validation & Review

All contributions should:
- Be readable without running code
- Have clear scope
- Avoid implicit side effects
- Preserve backward compatibility unless explicitly versioned

---

## Philosophy

StegDB exists so that **humans don’t have to remember rules**.

If a rule matters, it should live here.

---
