# 22. Standardization, Integration, and the Right Kind of Reuse

**Executive thesis:** Reuse is valuable when it preserves meaning; copying implementation without shared semantics often multiplies future integration work.

## Two enterprise axes

Integration answers how much business units must share state and coordinate transactions. Standardization answers how similarly they should operate. No Agent Coding adds a third practical question: which decisions can be compiled once and projected everywhere without erasing legitimate variation?

## Semantic reuse beats snippet reuse

A copied library can still be configured differently, wrapped inconsistently, or used under divergent assumptions. A reusable semantic contract states the capability, constraints, authority, inputs, outputs, refusals, evidence, and projection rules. Multiple implementations can satisfy it without losing interoperability.

## Class closure is the leverage point

The highest-value reuse closes a class. A marketplace pack, ontology profile, or generator can encode what the enterprise has learned so that new instances inherit the invariant. This is closer to an operating standard than to a code template.

## Operating practice

When teams ask for a shared library, first ask whether they actually need shared semantics, shared implementation, or both. Standardize the smallest layer that must remain invariant; project or implement the rest locally.

## Diagnostic question

Are teams asking for shared code when what they really need is a shared contract?

<!-- semantic-enrichment:v1 -->

## Operational significance

**22. Standardization, Integration, and the Right Kind of Reuse** is not retained as a label-only reference. This page defines a simulation contract rather than a claim that simulated success equals reality. A gym world must state its entities, state variables, actions, observation projections, information partitions, roles, policies, objective functions, authority boundaries, stochastic processes, and termination conditions. Without those dimensions a score is uninterpretable because the benchmark does not say what information or power the policy had.

## System contract

The useful algebra is `Episode = World × Roles × Policies × InformationPartitions × Authority`. Planner, policy, role, and agent remain distinct: a planner proposes; a policy maps admitted observations to candidate actions; a role describes responsibilities; an agent is an actor with bounded capabilities. Reward is evidence about the objective encoded by the environment, not permission to actuate outside it.

## Failure modes and falsifiers

Simulation is falsified by reality-model mismatch, leakage of privileged observations, an action projection that grants authority the real system does not have, reward hacking, nondeterministic fixtures without recorded seeds, or a scenario suite that excludes the failure class being claimed. The output should therefore include world identity, seed, policy identity, observation/action projections, result metrics, and a receipt that lets another runner reproduce the episode.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
