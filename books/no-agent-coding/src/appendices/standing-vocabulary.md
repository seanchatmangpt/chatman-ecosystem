# Appendix A. Standing Vocabulary

Standing is an evidence discipline, not a mood. Use the narrowest state supported by the exact subject and the exact verifier.

- **UNKNOWN** — the relevant subject was not observed, or evidence is stale, missing, or contradictory.
- **OBSERVED** — the subject was inspected or measured, without implying successful behavior.
- **CANDIDATE** — an artifact or plan exists for evaluation but has not earned the crown claim.
- **PARTIAL_ALIVE** — a bounded checkpoint executed successfully while a stronger claim remains open.
- **ALIVE** — the exact admitted subject executed and produced the claimed consequence under the owning verifier, with required receipt and replay evidence.
- **BLOCKED** — an admitted dependency or authority boundary prevents execution.
- **BUILD_BROKEN** — the requested verifier cannot be reached because the build path is broken.
- **UNSUPPORTED** — the capability lies outside the admitted boundary.
- **REFUSED_<TYPE>** — a typed policy, safety, authority, identity, or admission refusal.

A workflow definition is not a successful workflow run. A Git SHA is identity evidence, not runtime standing. Compilation is not deployment. An HTTP acknowledgment is not the postcondition. A generated artifact cannot certify its own generator.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix A. Standing Vocabulary** is not retained as a label-only reference. This page defines a simulation contract rather than a claim that simulated success equals reality. A gym world must state its entities, state variables, actions, observation projections, information partitions, roles, policies, objective functions, authority boundaries, stochastic processes, and termination conditions. Without those dimensions a score is uninterpretable because the benchmark does not say what information or power the policy had.

## System contract

The useful algebra is `Episode = World × Roles × Policies × InformationPartitions × Authority`. Planner, policy, role, and agent remain distinct: a planner proposes; a policy maps admitted observations to candidate actions; a role describes responsibilities; an agent is an actor with bounded capabilities. Reward is evidence about the objective encoded by the environment, not permission to actuate outside it.

## Failure modes and falsifiers

Simulation is falsified by reality-model mismatch, leakage of privileged observations, an action projection that grants authority the real system does not have, reward hacking, nondeterministic fixtures without recorded seeds, or a scenario suite that excludes the failure class being claimed. The output should therefore include world identity, seed, policy identity, observation/action projections, result metrics, and a receipt that lets another runner reproduce the episode.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
