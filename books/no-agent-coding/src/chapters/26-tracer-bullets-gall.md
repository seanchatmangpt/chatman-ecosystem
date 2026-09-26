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

<!-- semantic-enrichment:v1 -->

## Operational significance

**26. From Tracer Bullets to Gall Checkpoints** is not retained as a label-only reference. This page defines a simulation contract rather than a claim that simulated success equals reality. A gym world must state its entities, state variables, actions, observation projections, information partitions, roles, policies, objective functions, authority boundaries, stochastic processes, and termination conditions. Without those dimensions a score is uninterpretable because the benchmark does not say what information or power the policy had.

## System contract

The useful algebra is `Episode = World × Roles × Policies × InformationPartitions × Authority`. Planner, policy, role, and agent remain distinct: a planner proposes; a policy maps admitted observations to candidate actions; a role describes responsibilities; an agent is an actor with bounded capabilities. Reward is evidence about the objective encoded by the environment, not permission to actuate outside it.

## Failure modes and falsifiers

Simulation is falsified by reality-model mismatch, leakage of privileged observations, an action projection that grants authority the real system does not have, reward hacking, nondeterministic fixtures without recorded seeds, or a scenario suite that excludes the failure class being claimed. The output should therefore include world identity, seed, policy identity, observation/action projections, result metrics, and a receipt that lets another runner reproduce the episode.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
