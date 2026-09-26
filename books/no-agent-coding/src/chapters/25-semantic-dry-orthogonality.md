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

<!-- semantic-enrichment:v1 -->

## Operational significance

**25. Semantic DRY and Orthogonality** is not retained as a label-only reference. This page defines a simulation contract rather than a claim that simulated success equals reality. A gym world must state its entities, state variables, actions, observation projections, information partitions, roles, policies, objective functions, authority boundaries, stochastic processes, and termination conditions. Without those dimensions a score is uninterpretable because the benchmark does not say what information or power the policy had.

## System contract

The useful algebra is `Episode = World × Roles × Policies × InformationPartitions × Authority`. Planner, policy, role, and agent remain distinct: a planner proposes; a policy maps admitted observations to candidate actions; a role describes responsibilities; an agent is an actor with bounded capabilities. Reward is evidence about the objective encoded by the environment, not permission to actuate outside it.

## Failure modes and falsifiers

Simulation is falsified by reality-model mismatch, leakage of privileged observations, an action projection that grants authority the real system does not have, reward hacking, nondeterministic fixtures without recorded seeds, or a scenario suite that excludes the failure class being claimed. The output should therefore include world identity, seed, policy identity, observation/action projections, result metrics, and a receipt that lets another runner reproduce the episode.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
