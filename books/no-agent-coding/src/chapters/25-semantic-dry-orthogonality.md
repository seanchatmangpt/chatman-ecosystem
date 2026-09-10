# 25. Semantic DRY and Orthogonality

**Executive thesis:** The most expensive duplication is not duplicated code; it is duplicated decisions that can drift independently.

## DRY at the decision layer

Two code blocks may look different while encoding the same business rule. Conversely, identical libraries can be used under different semantics. Semantic DRY asks where knowledge is duplicated, then moves the invariant to one admitted source from which necessary representations are derived.

## Orthogonality through boundaries

Observation, admission, manufacture, verification, and actuation should be independently replaceable where their contracts permit. A graph engine should not silently own authority. A proof should not grant permission. A generator should not certify its own correctness. A transport should not define capability semantics.

## Why this matters organizationally

Semantic DRY reduces coordination load; orthogonality reduces blast radius. Together they let teams evolve projectors, runtimes, and interfaces without renegotiating the enterprise meaning of the capability on every change.

## Operating practice

When two teams must coordinate a change, ask whether they share a duplicated decision or a legitimate interface. Collapse duplicated decisions into a canonical semantic object. Keep legitimate implementation choices orthogonal behind that contract.

## Diagnostic question

Where is duplicated knowledge masquerading as merely duplicated code?
