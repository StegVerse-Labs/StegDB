# StegVerse Repo Minimum Standard (v1.0)

This standard defines the minimum structure that makes a StegVerse repository feel:
- intentionally designed
- currently usable (or clearly declared otherwise)
- aligned with StegVerse principles
- safe to evolve and extend

This is not a gatekeeping policy.
It is a shared clarity baseline.

---

## Core Principle

**Clarity beats polish.**

A repository may be incomplete or experimental and still meet this standard
if it is honest about status, has a clear entry point, and does not overclaim.

---

## Repo Types

Every repository should declare a type:

- **foundation**: principles, invariants, standards (e.g., StegSeed, StegCore)
- **identity**: identity / lineage / continuity (e.g., StegID, genealogy)
- **template**: user-installable templates (e.g., KnowledgeVault kits)
- **tooling**: scripts, automation, CI/CD, validators (e.g., StegDB tooling)
- **research**: papers, drafts, reading lists, figures
- **experiment**: prototypes and explorations
- **archive**: preserved historical materials

Declaring type improves comprehension and reduces misuse.

---

## Minimum Files (All Repos)

### 1) `README.md` (Required)
The README must answer, in plain language:

1. **What this is**
2. **What this is not**
3. **Current status**: `active | experimental | legacy | archived | mixed`
4. **How to start** (one “success path”)
5. **How it connects** to StegVerse (one paragraph)

**No false promises.** The README must match repo reality.

---

### 2) `STATUS.md` (Required)
A short status file that includes:

- `state:` active | experimental | legacy | archived | mixed
- `works_today:` yes/no and what “works” means
- `known_gaps:` 1–5 bullets
- `next_steps:` 1–5 bullets
- `last_reviewed_utc:` timestamp

This prevents ambiguity and reduces first-contact failure.

---

### 3) `LICENSE` (Recommended)
Use permissive licenses unless a repo explicitly requires otherwise.

If a repo does not yet have a license, it must say so in `STATUS.md`.

---

## Type-Specific Minimums

### A) Templates (User-Installable)
Templates must include:

- `WELCOME.md` (Required)
  - device-agnostic language
  - what the user is and is not being enrolled into
  - how to start in 30 seconds
- `vault_templates/` or `template/` folder (Recommended)
- a “download” or “copy folder to your device” instruction in README

Templates must not require proprietary software to read core content.

---

### B) Tooling / Automation Repos
Tooling repos must include:

- `CONTRACT.md` (Required)
  - inputs accepted
  - outputs produced
  - invariants
  - extension points
  - compatibility expectations

Tooling repos should include at least one CI “heartbeat” workflow.

---

### C) Foundation / Standards Repos
Foundation repos must include:

- `INVARIANTS.md` (Recommended)
  - what must never be violated
  - what can evolve
  - what is explicitly out of scope

Foundation repos should avoid executable enforcement where possible.

---

### D) Research Repos
Research repos must include:

- `README.md` with “how to navigate”
- `STATUS.md` with draft state
- clear separation between:
  - published
  - draft
  - notes
  - references

---

### E) Experimental Repos
Experimental repos must include:

- `STATUS.md` that clearly says “experimental”
- constraints and safety notes
- a statement that abandonment is acceptable

---

## CI Heartbeat (Recommended, not required)

Repos should have at least one automated check that demonstrates “life,” such as:

- markdown lint (optional)
- schema validation
- build bundle (for templates)
- smoke check

The purpose is to reduce uncertainty, not to enforce conformity.

---

## Canonical Documentation Overlay (Recommended)

When StegVerse-wide language needs to remain consistent (e.g., organization framing),
repos should reference canonical docs via StegDB overlay rules:

- prefer **link-only** references
- allow **excerpt** only for “front-door” repos

This prevents drift without forcing duplication.

---

## Standard of Honesty

A repo meets this minimum standard if:

- It has a clear entry point (`README.md`)
- It declares its state (`STATUS.md`)
- It does not overclaim
- It provides at least one success path OR explicitly says none exists yet
- It preserves future extensibility via a lightweight contract (type-dependent)

---

## Versioning

This minimum standard may evolve.

Repos are not required to retroactively “fix history,” but they should converge toward clarity over time.

---

## Final Note

StegVerse is designed to be replaceable.

This standard exists to make repos understandable today, without blocking better systems tomorrow.
