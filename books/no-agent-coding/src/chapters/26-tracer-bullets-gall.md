# 26. From Tracer Bullets to Gall Checkpoints

**Executive thesis:** A thin end-to-end slice is useful only when it crosses the real boundary and leaves evidence that can support the next layer.

## Why thin slices work

A tracer bullet reaches across architecture early enough to expose integration reality. Gall adds a stricter requirement: the slice must itself be a working system, not a mock of the future. It should reveal whether identities, contracts, runtime topology, authority, and evidence actually compose.

## Positive and negative evidence

A happy-path demo proves little if malformed or unauthorized cases also pass. Every Gall checkpoint should include a positive witness and a negative falsifier. The falsifier protects against vacuous tests and makes the boundary’s meaning explicit.

## Replay makes the slice cumulative

A checkpoint that only works in the originating agent session is not a stable foundation. Exact subject identity, deterministic receipt, and replay turn a thin slice into a pier that later complexity can safely depend on.

## Operating practice

Choose the smallest end-to-end capability that touches a real consumer. Use real boundaries where the claim names them. Record the exact command, output, subject digest, failure cases, and replay path before expanding the architecture.

## Diagnostic question

What end-to-end slice can cross a real consumer boundary and leave a replayable receipt?
