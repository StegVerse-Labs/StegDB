# Custody Transition Specification (v1)

This spec defines how custody changes are proposed, confirmed, contested,
and audited. Custody is not legal ownership. Custody is responsibility
for care/control and documentation continuity.

## Custody Transition States

A custody transition MUST be one of:

- proposed: initiated, not yet accepted
- acknowledged: current custodian has seen the proposal
- contested: current custodian disputes the proposal
- confirmed: transition accepted and becomes effective
- expired: proposal timed out with no confirmation
- revoked: proposal withdrawn by initiator before confirmation

## Transition Safety Rule

No custody change becomes effective unless confirmed by an allowed
confirmation rule (see "Confirmation Rules").

## Confirmation Rules (default)

A transition may be confirmed by:
- explicit confirmation by current custodian (preferred)
- dual confirmation (current + receiving custodian)
- escrow confirmation (optional, for organizations)
- evidence-backed confirmation (rare; requires policy override)

## Shared Presence Events (non-deterministic)

If multiple custody agents are present at the same time/place, this may
be recorded as a "shared presence" event. Shared presence is not proof
of transfer.

Shared presence is captured as an event that may increase the probability
of transfer if corroborated by documents (e.g., signed intake forms).

## Custody Event Types

Common event_type values:
- purchase_intake
- warranty_intake
- handoff_to_service
- return_to_owner
- shared_presence_claim
- custody_dispute_opened
- custody_dispute_resolved

## Required Fields (for transitions)

- transition_id
- item_id
- initiated_by
- proposed_new_custodian
- timestamp
- location (optional but recommended)
- confidence (optional, derived)

## Notes

Custody events must be append-only. Corrections occur via new events.
