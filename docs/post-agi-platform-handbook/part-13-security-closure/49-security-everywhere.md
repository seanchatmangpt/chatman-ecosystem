# 49. Security Is Not a Chapter

A conventional platform handbook can reserve a chapter for securing access because many security mechanisms are added to an already chosen architecture.

In a post-AGI constitution, security is a property of every morphism.

## Identity in every transition

Observation, admission, construction, delegation, actuation, receipt, and replay each operate on exact identities.

Ambiguous identity is not merely a data-quality problem. It is an authority risk because the system may apply a lawful operation to the wrong subject.

## Authority is typed

The SELECT/CONSTRUCT/DO separation prevents a reasoning system from acquiring consequence merely because it can imagine or construct the action.

The authority broker is therefore a security boundary embedded in the calculus rather than a later access-control layer.

## Capability bounding

Adapters should expose the smallest consequential surface necessary for their admitted operations. Broad credentials can exist underneath, but the brokered interface should narrow what is reachable.

This is capability security expressed structurally.

## Consequence bounding

Security policy should state not only who can invoke an operation but what consequence class the operation may produce.

For example, “can update configuration” is too broad if the update can also expand privilege, destroy evidence, or alter the authority system itself.

## Refusal is security behavior

Malformed, stale, duplicate, unauthorized, conflicting, and tampered inputs should produce typed refusals. A security boundary that only succeeds correctly but fails ambiguously is difficult to reason about under machine-scale traffic.

## Evidence is part of security

Receipts allow the system to distinguish an intended transition from an unreceipted side effect. Replay and causal evidence make post-event analysis deterministic enough to support automated containment and reconstitution.

## Security without model mind-reading

The architecture does not need to decide whether a model “intends harm” before enforcing the boundary. It decides whether the requested transition is admitted and authorized for the exact subject.

This makes the system less dependent on interpreting internal model state.

## Falsifier

Security is not constitutional if any adapter can create a new consequential path that bypasses exact identity, operational admission, or receipted authority because the adapter is considered trusted.

## Operational exercise

Review one end-to-end capability. At every morphism, write the identity, authority assumption, refusal mode, and evidence produced. Security gaps appear where one of those fields is implicit.