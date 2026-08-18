# 24. Air-Gapped Construction

A post-AGI system should not equate intelligence with continuous network access.

Air-gapped and offline environments are valuable because they force construction dependencies, toolchains, evidence, and authority boundaries to become explicit.

## CONSTRUCT should survive disconnection

Where the required knowledge and toolchain are present, the system should be able to manufacture candidate artifacts without contacting the eventual actuation substrate.

This is especially useful for sensitive cloud configurations, regulated environments, and adversarial analysis.

The pattern is:

\[
Ontology + Inputs + Toolchain \rightarrow CONSTRUCT \rightarrow Artifact + Evidence
\]

with DO deferred to a separate authorized boundary.

## Dependency closure

An offline construction capsule must identify its compiler, libraries, templates, ontology versions, schemas, validators, and other dependencies.

A build that silently fetches mutable external inputs is not fully reconstitutable.

Dependency closure is therefore both a supply-chain property and a replay property.

## Deterministic replay

Offline toolchains make it easier to distinguish source variation from network or service variation. Exact inputs can be replayed under the same toolchain capsule to verify whether manufacture is deterministic.

## Safe cloud manufacture

A powerful use of CONSTRUCT is to manufacture cloud-service configurations without granting the constructor access to the real cloud account.

The system can produce plans, policy proofs, synthetic OCEL histories, cost models, and GymAct results in isolation. A separate BRCE adapter later receives only the admitted intent required for real actuation.

This reduces the authority exposed to the reasoning system.

## Portable receipts

Evidence should cross the air gap with the artifact. Content identity, toolchain identity, proof results, and construction receipts let the actuation side verify what it received before granting any authority.

## Falsifier

An “air-gapped” construction is not closed if its correctness depends on mutable external state that is neither captured nor declared as an unresolved observation.

## Operational exercise

Take one cloud deployment class and attempt to construct everything short of provider actuation offline: semantic graph, generated configuration, policy checks, proof obligations, cost model, and synthetic execution. Record exactly which remaining observations truly require the live provider.