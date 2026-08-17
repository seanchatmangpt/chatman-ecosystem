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