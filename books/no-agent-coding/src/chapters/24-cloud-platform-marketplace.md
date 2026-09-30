# 24. Cloud, Platform, and Marketplace as Projections

**Executive thesis:** AWS, Azure, GCP, Kubernetes, Terraform, internal platforms, and commercial marketplaces should be treated as target geometries, not as the source of enterprise meaning.

## Provider syntax is not the operating model

Cloud APIs and marketplace schemas are powerful but vendor-specific representations. If the enterprise lets each provider define the canonical meaning of entitlement, deployment, identity, cost policy, or capability, multi-cloud strategy becomes repeated translation by people and agents.

## Model the invariant, project the provider

The semantic core can express the provider-independent capability and the provider-specific constraints separately. ggen then manufactures the appropriate target surface. This does not pretend providers are equivalent; it makes differences explicit as bounded projection rules rather than hidden in ad hoc code.

## Standing remains provider-specific

Deterministic manufacture cannot prove that an external provider accepted and realized a consequence. Real cloud, marketplace, or payment claims require observation at the provider boundary and exact-provider receipts. Projection standing and operational standing must remain distinct.

## Operating practice

For a multi-provider capability, define the invariant first, then model each provider’s divergence. Test both the common contract and the provider-specific falsifiers. Never promote successful local generation into a claim about external provider execution.

## Diagnostic question

Which provider-specific representation has accidentally become your enterprise source of truth?

<!-- semantic-enrichment:v1 -->

## Operational significance

**24. Cloud, Platform, and Marketplace as Projections** is not retained as a label-only reference. This page defines a simulation contract rather than a claim that simulated success equals reality. A gym world must state its entities, state variables, actions, observation projections, information partitions, roles, policies, objective functions, authority boundaries, stochastic processes, and termination conditions. Without those dimensions a score is uninterpretable because the benchmark does not say what information or power the policy had.

## System contract

The useful algebra is `Episode = World × Roles × Policies × InformationPartitions × Authority`. Planner, policy, role, and agent remain distinct: a planner proposes; a policy maps admitted observations to candidate actions; a role describes responsibilities; an agent is an actor with bounded capabilities. Reward is evidence about the objective encoded by the environment, not permission to actuate outside it.

## Failure modes and falsifiers

Simulation is falsified by reality-model mismatch, leakage of privileged observations, an action projection that grants authority the real system does not have, reward hacking, nondeterministic fixtures without recorded seeds, or a scenario suite that excludes the failure class being claimed. The output should therefore include world identity, seed, policy identity, observation/action projections, result metrics, and a receipt that lets another runner reproduce the episode.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
