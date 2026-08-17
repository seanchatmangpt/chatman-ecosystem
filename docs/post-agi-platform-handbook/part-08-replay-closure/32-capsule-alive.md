# 32. Capsule ALIVE

Hosted CI is convenient but not the only place truth can be established. A post-AGI factory benefits from portable, deterministic validation capsules that can prove as much as possible locally and offline.

A Capsule ALIVE model factors evidence into:

\[
Source\ Capsule \times Validation\ Pack \times Execution\ Mode \times Toolchain\ Capsule \rightarrow Receipt\ DAG
\]

## Source Capsule

The source capsule identifies the exact code, ontology, generated inputs, configuration, and other subject material required by the claim.

## Validation Pack

The validation pack contains the admitted checks: unit tests, integration tests, negative fixtures, SHACL shapes, proof obligations, benchmark tasks, or other validators.

A validator has its own identity and standing.

## Execution Mode

Some claims can be proven offline. Others require containers, a browser, a local cluster, external APIs, hardware, or a specific cloud. The execution mode states which environment was actually exercised.

## Toolchain Capsule

Compiler versions, package locks, runtimes, build images, and deterministic dependencies belong here.

The goal is not perfect hermeticity in every domain. The goal is to make the boundary explicit so evidence can be interpreted correctly.

## VERIFIER_ALIVE is not SUBJECT_ALIVE

A validated reusable test harness can have standing independent of the next subject it evaluates.

\[
VERIFIER\_ALIVE(v) \not\Rightarrow SUBJECT\_ALIVE(s)
\]

The verifier's standing allows us to trust its method under matching assumptions. The subject still has to be executed through it.

## Local evidence before hosted metadata

When the exact validation can be run locally, local execution provides faster evidence and avoids treating hosted workflow status as the source of truth.

GitHub CI then becomes additional exact-head publication evidence rather than the only proof that the project works.

## Falsifier

A capsule is not reusable if it hides material external dependencies whose identity can change between runs without changing the capsule receipt.

## Operational exercise

Package one project's narrowest behavioral acceptance test as a capsule. Record source, validator, toolchain, execution mode, and output receipt. Then test whether a second machine can reproduce the same evidence without relying on undocumented state.