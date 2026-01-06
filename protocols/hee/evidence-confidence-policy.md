# HEE Evidence Confidence Policy (v1)

This policy defines how evidence is scored, how confidence is represented,
and what evidence may be asserted in escalation packets.

## Core Rule
Evidence may be ingested at any confidence level. Evidence may only be
ASSERTED in an escalation packet if it meets the eligibility threshold
for that escalation level.

Low-confidence evidence may be stored, referenced internally, or used to
guide investigation, but it must not be used as the basis for claims.

## Confidence Representation

Confidence is represented as:

- score: float in [0.0, 1.0]
- band: one of {weak, moderate, strong, very-strong}
- rationale: machine-readable list of factors

Bands:
- weak:        0.00–0.29
- moderate:    0.30–0.59
- strong:      0.60–0.79
- very-strong: 0.80–1.00

## Default Eligibility Thresholds (by escalation level)

- Level 1 (counterparty / warranty / dealer):         score >= 0.40
- Level 2 (corporate escalation / supervisor):        score >= 0.60
- Level 3 (regulator / formal complaint):             score >= 0.75
- Level 4 (legal counsel / court-ready packet):       score >= 0.85

## Evidence Categories

Each artifact is categorized at ingestion:
- photo
- video
- document
- communication
- estimate
- contract
- report
- log

## Confidence Factors (non-exhaustive)

The confidence score is derived from observable properties such as:
- metadata integrity (e.g., EXIF present vs stripped)
- ingestion proximity to creation time
- transformation history (original vs re-export vs screenshot-of-screenshot)
- corroboration (independent artifacts supporting same claim)
- counterparty acknowledgment or dispute status

## Escalation Packet Assertion Rules

When generating a packet:
- Include only artifacts meeting the threshold as "asserted evidence"
- Optionally include sub-threshold artifacts in a separate section labeled
  "non-asserted context" (default: OFF)
- Never present sub-threshold evidence as proof

## Auditability

Every confidence score must include:
- computed_at timestamp
- algorithm_version
- factor list

Scores may be recomputed later; prior computed values remain preserved
in history for audit.
