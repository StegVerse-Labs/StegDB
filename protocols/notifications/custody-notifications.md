# Custody Change Notification Policy (v1)

This policy governs when and how an owner/custodian is notified about
custody-related actions.

## Notification Events

Notify on:
- custody_transition_proposed
- custody_transition_acknowledged (optional)
- custody_transition_contested
- custody_transition_confirmed
- custody_transition_expired
- custody_transition_revoked

## Default Notification Rules

- Always notify the current custodian when a transition is proposed.
- Always notify the current custodian when a transition is confirmed.
- Always notify the current custodian when a transition is contested.

## Privacy Constraints

Notifications must NOT include:
- initiator private contact details (unless already shared by user)
- financial details
- escalation strategy
- analysis conclusions

Notifications may include:
- item nickname/model
- transition type (proposed/confirmed/etc.)
- timestamp
- coarse location (city/state or “at service center”)
- required action (“Review / Confirm / Contest”)

## Abuse Mitigations

- Rate limit custody proposals per initiator
- Flag repeated failed proposals
- Allow custodian to temporarily lock custody transitions
- Log all attempts immutably

## Suggested Message Copy (default)

Title: Custody Change Proposed  
Body: A custody change was proposed for [ITEM]. No change is final unless
you confirm. Review details and confirm or contest.
