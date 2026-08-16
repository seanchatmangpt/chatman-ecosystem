# 69. Experimental Method, Falsification, and Benchmark Design

A constitutional architecture can become unfalsifiable if every failure is attributed to an implementation defect and every success is attributed to the architecture. This chapter defines an experimental discipline intended to prevent that.

## 69.1 Unit of experiment

Every experiment must name an exact subject

\[
s=(repo,sha,config,ontology,policy,capability,environment).
\]

Results without immutable subject identity are observations, not crown evidence.

## 69.2 Hypothesis tuple

Represent each experiment as

\[
X=(H_1,H_0,M,I,C,P,F,R),
\]

where:

- \(H_1\): architectural hypothesis;
- \(H_0\): null hypothesis;
- \(M\): metrics;
- \(I\): intervention;
- \(C\): controls;
- \(P\): protocol;
- \(F\): falsifier;
- \(R\): receipt bundle.

A benchmark without a falsifier is a demonstration.

## 69.3 Required baselines

At least four baseline families should be considered where applicable:

1. human/manual workflow;
2. conventional scripted automation;
3. unconstrained or conventional agentic implementation;
4. Chatman constitutional implementation.

The purpose is not to prove that one paradigm wins universally. It is to identify the workloads where its additional structure buys measurable value.

## 69.4 Ablation studies

The architecture has multiple mechanisms. Remove them one at a time.

### Ablation A — No semantic source

Maintain representations independently. Measure drift and repair arrivals.

### Ablation B — No separate operational admission

Allow verified candidates to actuate directly. Measure accidental/unauthorized consequence under fault injection.

### Ablation C — No receipt requirement

Execute the same workflow without causal receipt closure. Measure replay and diagnosis quality.

### Ablation D — Single-plan search instead of DfCM

Measure recovery and solution quality under injected topology failures.

### Ablation E — Instance tests without class-transfer tests

Measure generalization failure on novel members of the same admitted class.

If removing a mechanism causes no measurable degradation across representative tasks, that mechanism's necessity claim weakens.

## 69.5 Fault injection

A serious autonomous-systems benchmark should inject failures at constitutional boundaries:

- stale observation;
- contradictory source evidence;
- malformed projection;
- verifier false positive/negative;
- expired capability;
- wrong subject SHA;
- replay/provenance mismatch;
- partial network failure;
- adversarial candidate;
- event-log omission;
- dependency version drift.

Measure whether failures are localized to typed refusals or leak into consequential state.

## 69.6 Transfer protocol

For class \(c\), partition instances into discovery and transfer sets:

\[
D_c\cap T_c=\varnothing.
\]

Use \(D_c\) to construct the semantic solution structure. Freeze it. Then evaluate \(T_c\) without semantic rediscovery.

Class closure is supported when

\[
Success(T_c\mid FrozenClassModel_c)
\]

meets the declared threshold.

This is stricter than replay and essential for claims of reusable autonomy.

## 69.7 Reproducibility levels

Define a ladder:

- **R0 — Narrative:** claim described.
- **R1 — Subject identified:** exact revision/config known.
- **R2 — Locally reproducible:** independent rerun succeeds.
- **R3 — Environment portable:** succeeds under a second compatible environment.
- **R4 — Transfer:** succeeds on distinct class instances.
- **R5 — Adversarially robust:** survives declared fault/attack set.

`ALIVE` should always state which reproduction level it denotes.

## 69.8 Statistical treatment

Deterministic paths still require statistical analysis when environments, workloads, or competitors vary. For repeated trials report distributions, confidence intervals, failure rates, and effect sizes rather than only best runs.

For metric \(m\), compare treatment \(T\) and baseline \(B\) using an effect such as

\[
\Delta_m=\mathbb E[m_T]-\mathbb E[m_B].
\]

For tail-sensitive operations, report quantiles such as \(p95\) and \(p99\), not only means.

## 69.9 Negative results

Negative results are first-class outputs. A typed negative result should identify:

- exact subject;
- violated assumption;
- observed counterexample;
- whether the failure refutes architecture, implementation, or stated scope;
- what would have to change for retest.

This prevents the research program from becoming self-sealing.

## 69.10 Crown criterion

A PhD-grade crown result is not “the demo worked.” It is:

> **An exact-subject, independently checkable, falsifier-bearing result whose scope is explicit, whose alternative explanations are controlled, whose consequence is receipted where applicable, and whose transfer boundary is measured.**