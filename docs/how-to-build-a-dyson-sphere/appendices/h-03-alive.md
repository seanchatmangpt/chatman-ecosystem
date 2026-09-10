# Appendix H.3 — ALIVE

**Parent:** [Appendix H — Status and Refusal Taxonomy](h-status-and-refusal-taxonomy.md)

Standing belongs to an exact subject. Inspection is not execution, execution is not verification, and a named receipt file is not evidence that the intended transition occurred. A useful receipt binds identity, authority, consequence, verifier result, and replay instructions so a later observer can reconstruct why the standing claim was made.

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix H.3 — ALIVE** is not retained as a label-only reference. Standing is a type over evidence, not a progress adjective. UNKNOWN means the required observation has not closed. PARTIAL_ALIVE means some bounded behavior has executed but the requested crown has not. ALIVE is reserved for the exact admitted subject executing successfully against the required verifier. BLOCKED identifies a known external or authority obstruction; BUILD_BROKEN names a concrete build failure; UNSUPPORTED says the requested capability is outside the implementation; typed REFUSED records a lawful denial.

## System contract

Statuses do not automatically promote. Source inspection cannot produce ALIVE; the existence of a workflow cannot produce ALIVE; a unit test cannot crown a real integration; a simulation cannot crown deployment. Promotion requires evidence whose subject, environment, command, verifier, and result intersect the claim. Demotion is equally important: changed identity, stale evidence, failed replay, or a newly observed contradiction lowers standing rather than being hidden by a previous green run.

## Failure modes and falsifiers

A status page is useful when it tells the reader exactly what evidence would change the type. For each state, name the missing edge, the next lawful observation or execution, and the falsifier. This makes status operational: another system can decide whether to observe, repair, refuse, or re-run without interpreting a vague confidence score.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
