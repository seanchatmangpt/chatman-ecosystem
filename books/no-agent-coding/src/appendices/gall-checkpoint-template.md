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

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix B. Gall Checkpoint Template** is not retained as a label-only reference. This page defines a simulation contract rather than a claim that simulated success equals reality. A gym world must state its entities, state variables, actions, observation projections, information partitions, roles, policies, objective functions, authority boundaries, stochastic processes, and termination conditions. Without those dimensions a score is uninterpretable because the benchmark does not say what information or power the policy had.

## System contract

The useful algebra is `Episode = World × Roles × Policies × InformationPartitions × Authority`. Planner, policy, role, and agent remain distinct: a planner proposes; a policy maps admitted observations to candidate actions; a role describes responsibilities; an agent is an actor with bounded capabilities. Reward is evidence about the objective encoded by the environment, not permission to actuate outside it.

## Failure modes and falsifiers

Simulation is falsified by reality-model mismatch, leakage of privileged observations, an action projection that grants authority the real system does not have, reward hacking, nondeterministic fixtures without recorded seeds, or a scenario suite that excludes the failure class being claimed. The output should therefore include world identity, seed, policy identity, observation/action projections, result metrics, and a receipt that lets another runner reproduce the episode.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
