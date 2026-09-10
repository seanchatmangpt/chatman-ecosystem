# Appendix N — Typed Refusal Taxonomy

Illustrative refusal classes:

- `REFUSED_MALFORMED_INPUT`
- `REFUSED_IDENTITY_MISMATCH`
- `REFUSED_STALE_SUBJECT`
- `REFUSED_SCHEMA_VIOLATION`
- `REFUSED_POLICY_VIOLATION`
- `REFUSED_MISSING_AUTHORITY`
- `REFUSED_SCOPE_WIDENING`
- `REFUSED_CONFLICTING_EVIDENCE`
- `REFUSED_DUPLICATE_ACTUATION`
- `REFUSED_TAMPERED_EVIDENCE`
- `REFUSED_POSTCONDITION_MISMATCH`
- `REFUSED_CLASS_NOT_APPLICABLE`

The exact enum belongs to the owning implementation. The principle is that refusal preserves causal information.

## Distinguish lifecycle states

`UNSUPPORTED` means the capability is not available.

`BLOCKED` means a known dependency prevents advancement.

`REJECTED` is a standing decision about a subject or candidate.

These should not be collapsed into generic refusal unless the owning ontology explicitly defines the mapping.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix N — Typed Refusal Taxonomy** is not retained as a label-only reference. This page sits on the irreversible boundary between choosing a possibility and changing the world. SELECT, CONSTRUCT, and DO are separate authorities. Search may explore many reversible candidates; construction may manufacture an artifact or counterfactual; only an explicitly admitted grant for the exact subject and consequence class can authorize DO. Access to a connector, credential, model, or command runner is capability—not authority.

## System contract

The brokered sequence is `intent -> exact-subject admission -> authority check -> consequence bound -> receipt reservation -> actuator -> observation -> reconciliation -> final receipt`. Relevant UNKNOWN refuses before DO. Ambiguous actuation does not turn into a retry loop. Replay verifies prior evidence and intentionally lacks an actuator edge. These separations keep autonomous operation from becoming ambient permission.

## Failure modes and falsifiers

Permanent falsifiers include accepting a nearby authority class, allowing a grant for one subject to mutate another, invoking an actuator before reservation is durable, promoting transport ACK to DONE, or letting a planner/model/hook manufacture its own authority. Any such edge is a constitutional defect even if the resulting state happens to be desirable.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
