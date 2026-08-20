# Appendix B. Gall Checkpoint Template

Use this template to turn a thin slice into a predecessor that later complexity may lawfully depend on.

## Subject

Record repository, ref, exact commit or content digest, toolchain identity, and relevant environment identity.

## Boundary

State the one capability claim being tested and the real consumer or external boundary named by that claim. Exclude stronger claims explicitly.

## Positive witness

Define the smallest input that must produce the claimed consequence. Capture the exact command and observed result.

## Negative falsifier

Define at least one malformed, unauthorized, stale, contradictory, or otherwise invalid case that must refuse. A test suite without a falsifier can be vacuous.

## Receipt

Bind subject identity, authority class, inputs, outputs, consequence evidence, verifier, timestamps where relevant, and a claim ceiling.

## Replay

Provide a deterministic replay path that does not depend on the originating human or agent session. Replay should avoid consequential re-actuation unless that re-actuation is explicitly safe and authorized.

## Promotion rule

Promote from UNKNOWN or CANDIDATE only to the strongest state supported by the executed evidence. Do not use milestone pressure to skip states.
