# 2. From O to O*

Observation is necessary but insufficient for manufacture.

The transition from `O` to `O*` is the first constitutional gate:

\[
O \xrightarrow{\operatorname{admit}} O^*
\]

Admission does not mean that every observation is true. It means that a bounded set of observations has been aligned to an exact subject, grounded in admissible evidence, constrained to a declared scope, and accepted for a particular downstream purpose.

## Admission is a typed transformation

A post-AGI system may hold enormous amounts of information. Only a small portion should participate in a particular actuation.

For subject `s`, context `Γ`, and policy `Π`, admission can be modeled as a partial function:

\[
\operatorname{admit}_{\Gamma,\Pi}(O,s) \rightharpoonup O^*
\]

The function is partial because refusal is lawful. A system should prefer a typed refusal to silently manufacturing from incompatible evidence.

## Four admission obligations

**Alignment** asks whether observations refer to the same subject and semantic frame. A Git SHA, image digest, deployment UID, cloud resource ID, and service name must be related explicitly rather than merged by naming coincidence.

**Grounding** asks what evidence supports each admitted proposition. Model output may suggest a relationship, but the relationship must remain `INFERRED` until grounded by the accepted evidence policy.

**Bounding** states where the claim applies: repository, branch, commit, account, region, namespace, tenant, time interval, version, capability, or transaction.

**Authority context** establishes what downstream operations the admitted subject may participate in. Admission to reason about a system is not admission to change it.

## Refusal preserves information

Refusal is not a dead end. A typed refusal narrows the graph.

Examples include:

- `REFUSED_STALE_SUBJECT`
- `REFUSED_IDENTITY_MISMATCH`
- `REFUSED_MISSING_AUTHORITY`
- `REFUSED_SCHEMA_VIOLATION`
- `REFUSED_CONFLICTING_EVIDENCE`
- `REFUSED_TAMPERED_RECEIPT`

A refusal records why an edge cannot currently advance. DfCM then preserves all other lawful edges.

## Admission replaces the hidden human meeting

In conventional organizations, admission is often implicit. An engineer reads a ticket, checks Slack, asks a teammate, looks at a dashboard, assumes the latest branch is correct, and begins changing infrastructure. The human performs a private, lossy admission function in their head.

Post-AGI manufacture cannot depend on that hidden step. The admission decision must be inspectable and replayable.

That is why a ticket must become deterministic before it can crown a subject. Natural language may initiate SELECT and CONSTRUCT, but consequential DO requires a bounded admitted carrier.

## The critical non-implications

\[
O \not\Rightarrow O^*
\]

\[
O^* \not\Rightarrow A
\]

\[
A_{candidate} \not\Rightarrow \operatorname{authority}(DO)
\]

These non-implications are more important in a post-AGI system than any particular model architecture. Capability can increase without erasing the boundaries.

## Falsifier

If two distinct exact subjects can be admitted as one merely because their human-readable labels match, the admission system is unsound for exact-subject standing.

## Operational exercise

Choose an existing deployment workflow and write the admission record it currently leaves implicit. Identify the subject identity, evidence sources, policy version, expected postcondition, authority scope, and expiration. Anything missing is not “probably fine”; it is a named gap in `O*`.