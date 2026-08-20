# Appendix K — CLI/API/MCP/A2A Projection Matrix

| Semantic concern | CLI | API | MCP | A2A |
|---|---|---|---|---|
| Capability identity | command id | operation/resource id | tool/resource id | capability id |
| Input schema | args/flags | request schema | tool schema | task/message schema |
| Exact subject | explicit flag or file | typed field | typed field | delegated subject |
| Refusal | exit/status + typed body | typed error | typed tool result/error | typed task refusal |
| Authority | request only | request only | intent only | delegated scope |
| DO | BRCE | BRCE | BRCE | BRCE |
| Receipt | machine-readable output | response/reference | tool result/reference | returned evidence chain |
| Replay | command + subject capsule | request capsule | intent capsule | delegation + evidence capsule |

The exact protocol syntax may evolve. Semantic correspondence is the invariant.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix K — CLI/API/MCP/A2A Projection Matrix** is not retained as a label-only reference. An interface projection is one view of a capability algebra, not a new owner of the underlying semantics. CLI, HTTP, MCP, A2A, UI, workflow, and library surfaces should project the same capability identity, parameters, authority requirements, refusal modes, evidence, and standing. A surface-specific convenience must not create a privileged path that bypasses admission or receipts.

## System contract

The projection matrix should therefore answer more than 'is there an endpoint?'. For each capability it should identify transport, input schema, authentication, exact authority class, idempotency semantics, timeout/ambiguity behavior, postcondition verifier, receipt identity, and replay route. Missing cells are explicit UNSUPPORTED/PARTIAL_ALIVE states rather than assumed parity.

## Failure modes and falsifiers

The strongest falsifier is semantic non-equivalence: two interfaces invoke what is nominally the same capability but differ in authorization, defaults, validation, or outcome interpretation. Contract tests should run equivalent requests through each available projection and compare normalized intents and receipts, while still preserving transport-specific evidence.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
