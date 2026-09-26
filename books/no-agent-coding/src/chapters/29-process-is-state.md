# 29. Process Is State: OCEL and Executable Memory

**Executive thesis:** For consequential systems, the path by which a state was reached can be part of the state’s standing.

## Endpoint equality is insufficient

Two environments can look identical at a snapshot while having different authority histories, approvals, source identities, or manufacturing paths. If standing depends on those facts, the process trajectory cannot be discarded as mere logging.

## OCEL as evidence carrier

Object-Centric Event Logs can represent events involving multiple business objects without forcing every process into one flat case identifier. In the Chatman Ecosystem, OCEL is useful as a process-evidence surface: what object changed, through which transition, under which identities, and in what order.

## Analysis remains a separate court

Emitting process evidence is not the same as proving conformance. Discovery, fitness, precision, variants, and formal process checks should be owned by independent analysis surfaces. The producer should not certify its own process merely because it emitted events.

## Operating practice

For a high-consequence capability, define which events and objects must exist for replay. Capture enough process identity to distinguish lawful and unlawful routes to the same endpoint. Keep emission, analysis, and actuation authority separate.

## Diagnostic question

Which endpoint states need process history before their standing is meaningful?

<!-- semantic-enrichment:v1 -->

## Operational significance

**29. Process Is State: OCEL and Executable Memory** is not retained as a label-only reference. This page defines a simulation contract rather than a claim that simulated success equals reality. A gym world must state its entities, state variables, actions, observation projections, information partitions, roles, policies, objective functions, authority boundaries, stochastic processes, and termination conditions. Without those dimensions a score is uninterpretable because the benchmark does not say what information or power the policy had.

## System contract

The useful algebra is `Episode = World × Roles × Policies × InformationPartitions × Authority`. Planner, policy, role, and agent remain distinct: a planner proposes; a policy maps admitted observations to candidate actions; a role describes responsibilities; an agent is an actor with bounded capabilities. Reward is evidence about the objective encoded by the environment, not permission to actuate outside it.

## Failure modes and falsifiers

Simulation is falsified by reality-model mismatch, leakage of privileged observations, an action projection that grants authority the real system does not have, reward hacking, nondeterministic fixtures without recorded seeds, or a scenario suite that excludes the failure class being claimed. The output should therefore include world identity, seed, policy identity, observation/action projections, result metrics, and a receipt that lets another runner reproduce the episode.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
