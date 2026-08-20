# Appendix G — BRCE Reference

This appendix is a reusable reference surface for the manuscript. It is intentionally explicit about scope and evidence: examples illustrate representation and reasoning; they do not claim that a physical Dyson system has been built, tested, or admitted.

SELECT, CONSTRUCT, and DO are separate authority classes. A planner may rank candidates; a constructor may render them; only a brokered authority path may cause consequence. BRCE enforces zero unreceipted actuation by binding intent, subject, authority, preconditions, execution result, postconditions, and replay metadata into a receipt.

## Sections

- [Admission](g-01-admission.md)
- [Authority](g-02-authority.md)
- [Actuation](g-03-actuation.md)
- [Receipt](g-04-receipt.md)
- [Replay](g-05-replay.md)
- [Refusal](g-06-refusal.md)

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix G — BRCE Reference** is not retained as a label-only reference. This page sits on the irreversible boundary between choosing a possibility and changing the world. SELECT, CONSTRUCT, and DO are separate authorities. Search may explore many reversible candidates; construction may manufacture an artifact or counterfactual; only an explicitly admitted grant for the exact subject and consequence class can authorize DO. Access to a connector, credential, model, or command runner is capability—not authority.

## System contract

The brokered sequence is `intent -> exact-subject admission -> authority check -> consequence bound -> receipt reservation -> actuator -> observation -> reconciliation -> final receipt`. Relevant UNKNOWN refuses before DO. Ambiguous actuation does not turn into a retry loop. Replay verifies prior evidence and intentionally lacks an actuator edge. These separations keep autonomous operation from becoming ambient permission.

## Failure modes and falsifiers

Permanent falsifiers include accepting a nearby authority class, allowing a grant for one subject to mutate another, invoking an actuator before reservation is durable, promoting transport ACK to DONE, or letting a planner/model/hook manufacture its own authority. Any such edge is a constitutional defect even if the resulting state happens to be desirable.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
