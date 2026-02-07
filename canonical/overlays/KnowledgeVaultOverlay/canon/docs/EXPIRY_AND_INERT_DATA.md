# Expiry & Inert Data (v1)

## Requirement
When data is used under a contract, that contract must define:
- expiry time (or conditions)
- post-expiry behavior
- what “inert” means in practice

## “Inert” definition (v1)
After expiry, the recipient must not:
- continue to serve or redistribute the content
- keep plaintext access
- use it for new derivatives

Permitted after expiry:
- retaining a non-reversible audit receipt (hash + metadata)
- retaining aggregated stats that cannot reconstruct content
