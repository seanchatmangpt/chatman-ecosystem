# 30. Replay as a Constitutional Primitive

Logging remembers that something happened. Retry attempts an operation again. Replay reconstructs a transition from preserved identity, inputs, context, and law.

Those are different functions.

## Replay has a subject

A replayable operation identifies the original subject and the replay subject separately.

If the world has changed, a literal repetition may no longer be lawful. The system must decide whether it is replaying the same closed computational capsule, reproducing an equivalent class instance, or attempting a new actuation under current conditions.

## Deterministic replay

For pure manufacture, the strongest target is deterministic reconstruction:

\[
\mu_{T,C}(O^*) = A
\]

where `T` is the exact toolchain and `C` is relevant configuration. Repeating the operation under the same identities should reproduce the expected artifact or explain why not.

## Operational replay is more constrained

Real-world actions are not generally safe to repeat blindly. Sending the same payment, deleting the same resource, or issuing the same physical command can have different consequences the second time.

Operational replay therefore often means replaying the **decision and evidence path** while assigning a new idempotency or authority context to any new DO.

## Hooks do not replay authority

A historical receipt can prove that an operation was authorized then. It does not automatically grant authority now.

Replay must re-evaluate time-sensitive policy and operational admission unless the authority itself was explicitly designed to be replayable.

## Replay as debugging

When a post-AGI system produces an unexpected outcome, replay narrows the causal search. If the source, toolchain, validator, and configuration reproduce the candidate but the external postcondition differs, the fault lies beyond the construction capsule.

This is much more precise than rerunning an unchanged workflow hoping the failure disappears.

## Falsifier

A claimed replay is not replay if material inputs, toolchain, or subject identity are unknown and the system merely performs a similar operation again.

## Operational exercise

Pick one recent successful deployment. Determine whether you can reconstruct the candidate artifact exactly. Then determine whether you can reconstruct the decision to deploy it without automatically redeploying. Those are two different replay capabilities.