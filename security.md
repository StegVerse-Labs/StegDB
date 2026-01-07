# Security Policy (StegDB)

StegDB defines canonical protocols and schemas used across StegVerse.

## Reporting a Vulnerability
If you believe you’ve found a vulnerability or abuse vector (custody manipulation, confidence scoring bypass, notification abuse, schema injection, etc.):

1. **Do not open a public issue with exploit details.**
2. Share a minimal description and impact:
   - What can be abused
   - What data/behavior is impacted
   - Reproduction steps (safe + minimal)
3. Include affected paths (e.g., `/protocols/custody/*`, `/protocols/hee/*`).

## Scope
In scope:
- Custody semantics
- Evidence confidence policy
- Notification thresholds/rules
- Schema validation and ingestion

Out of scope:
- Consumer incident evidence and letters (belongs in consumer repos)

## Fix Philosophy
We prioritize:
- Additive changes
- Versioned protocols
- Backward compatible schema evolution where possible
