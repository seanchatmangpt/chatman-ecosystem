# 28. ALIVE Is an Epistemic Type

Engineering organizations routinely use “done,” “working,” “green,” and “deployed” as conversational summaries. At post-AGI scale, those words must become typed claims.

`ALIVE` is not praise. It is evidence-backed standing for an exact subject.

## Standing vocabulary

The repository constitution distinguishes states such as:

- `UNKNOWN` — insufficient admitted evidence;
- `OBSERVED` — the subject or behavior has been directly observed;
- `CANDIDATE` — a subject is proposed for advancement but has not satisfied crown obligations;
- `PARTIAL_ALIVE` — some required evidence is established while material gates remain;
- `ALIVE` — all required gates for the bounded claim have passed against the exact subject;
- `BLOCKED` — advancement depends on an unresolved external condition;
- `UNSUPPORTED` — the required capability is not currently supported;
- `REJECTED` — the subject has been deliberately excluded;
- `SUPERSEDED` — another subject has replaced its standing.

Typed refusal remains separate from these lifecycle standings.

## Inspection is not execution

Reading a source file proves that the file exists and contains certain text. It does not prove runtime behavior.

Compiling code proves that one compiler accepted one source/configuration context. It does not prove the requested CLI behavior, service integration, or real external actuation.

A workflow definition proves that automation is described. It does not prove a successful workflow run.

An HTTP 200 proves only the semantics guaranteed by that endpoint, not whatever broader business outcome the caller hoped occurred.

## Exact subject law

Standing attaches to identity.

\[
ALIVE(s_1) \not\Rightarrow ALIVE(s_2)
\]

unless an explicit equivalence or transfer rule has been admitted.

This prevents stale CI, cached artifacts, and neighboring branches from being used as evidence for a changed subject.

## Checkpoint is not crown

A successful unit test is a checkpoint. A formal proof is a checkpoint. A GymAct score is a checkpoint. Exact-head CI is a checkpoint.

The crown is the conjunction of the gates required by the claim.

No individual checkpoint should silently expand its scope.

## Falsifier

If a system can assign `ALIVE` from narrative, inspection, or inherited reputation without observed execution required by the claim, the standing type has collapsed.

## Operational exercise

Take five projects currently described as “working.” For each, name the exact subject and evidence ladder. Reclassify them without using narrative confidence. The gaps are more valuable than an inflated green portfolio.