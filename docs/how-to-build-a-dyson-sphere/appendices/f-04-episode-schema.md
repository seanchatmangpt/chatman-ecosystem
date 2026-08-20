# Appendix F.4 — Episode Schema

**Parent:** [Appendix F — gymact Environment](f-gymact-environment.md)

GymAct provides counterfactual execution before physical consequence. A world model names its state, roles, policies, observation projections, action projections, authority, and episode boundaries. Simulation can falsify a candidate or expose missing constraints, but it cannot prove the physical world will behave identically; its standing is experimental evidence, not deployment evidence.

## Minimal record

```text
subject = <exact identity>
observed = <bounded inputs>
admitted = <constraints and uncertainty>
authority = <SELECT|CONSTRUCT|DO>
executed = <observed action or NONE>
verified = <postcondition evidence>
receipt = <content identity>
replay = <deterministic reconstruction method>
standing = <bounded status>
```

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix F.4 — Episode Schema** is not retained as a label-only reference. This page defines a simulation contract rather than a claim that simulated success equals reality. A gym world must state its entities, state variables, actions, observation projections, information partitions, roles, policies, objective functions, authority boundaries, stochastic processes, and termination conditions. Without those dimensions a score is uninterpretable because the benchmark does not say what information or power the policy had.

## System contract

The useful algebra is `Episode = World × Roles × Policies × InformationPartitions × Authority`. Planner, policy, role, and agent remain distinct: a planner proposes; a policy maps admitted observations to candidate actions; a role describes responsibilities; an agent is an actor with bounded capabilities. Reward is evidence about the objective encoded by the environment, not permission to actuate outside it.

## Failure modes and falsifiers

Simulation is falsified by reality-model mismatch, leakage of privileged observations, an action projection that grants authority the real system does not have, reward hacking, nondeterministic fixtures without recorded seeds, or a scenario suite that excludes the failure class being claimed. The output should therefore include world identity, seed, policy identity, observation/action projections, result metrics, and a receipt that lets another runner reproduce the episode.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
