# 28. Zero Unreceipted Actuation

> **Program relation.** This chapter is part of the Chateco doctoral program. It preserves the native research object before mapping it into the constitutional manufacturing calculus. The preserved source anchor for this chapter is **19.6 Zero Unreceipted Actuation** from the doctoral thesis corpus. It is evidence-bearing source material for the chapter, not an assertion that the chapter title and source heading are definitionally equivalent.

## Research claim

**Zero Unreceipted Actuation** is treated here as a law-state problem rather than a slogan. The chapter asks which observations are admissible, which transformations are lawful, what authority is required for consequence, which receipts establish standing, and what replay or transfer would be required to keep that standing over time. The Chateco position is deliberately bounded: adjacency is not equivalence, execution is not proof, and absence of evidence does not become refusal by narration.

## Preserved source development

This section establishes **19.6 Zero Unreceipted Actuation** as a distinct law-state problem inside authorization and brokered actuation. Its native objects are diagnoses, intents, plans, grants, capabilities, brokers, adapters, mutations, artifacts, and receipts. The analysis preserves those objects before mapping them to the Chatman Equation; the equation is not allowed to erase domain structure merely to obtain a verbal match.

The central proposition is that 19.6 Zero Unreceipted Actuation receives standing only when the relevant observation is admitted, the transformation is lawful for the declared boundary, and the consequence is connected to a receipt. In this domain, manufacture includes routing, policy evaluation, authorization, broker dispatch, actuation, and reconciliation.

### Preserve

The preserved domain includes diagnoses, intents, plans, grants, capabilities, brokers, adapters, mutations, artifacts, and receipts. Each object retains its own identity, lifecycle, authority, and failure conditions. A mapping is admissible only when it preserves the native distinction between what exists, what is observed, what is authorized, what changes, and what the institution or verifier recognizes afterward.

The strongest live claim is retained: the artifact need not be a file. It may be a graph, proof, plan, capability, changed relationship, deployed resource, or physical event. The invariant concerns the lawful production of consequence, not a preferred substrate.

### Fence

The boundary for this section excludes semantic inflation. A recognized token is not necessarily a supported feature. A generated string is not necessarily a proof. A completed physical movement is not necessarily authorized. A log line is not necessarily an adequate receipt. The domain-specific failure to avoid is that intent, recommendation, or proof is allowed to mutate state without a separate authority boundary.

Claims are classified as demonstrated, inferred, proposed, unknown, or unsupported. `UNKNOWN` is not promoted into `ADMITTED`; `UNSUPPORTED` is not rewritten as a refusal of the underlying proposition. These distinctions are part of the result rather than editorial caution added afterward.

### Calculus

The local projection is written as

\\\[ O \\xrightarrow{\\operatorname{admit}} O\^\* \\xrightarrow{\\mu} A \\xrightarrow{\\operatorname{receipt}} R. \\\]

Here, admission means a grant tied to a specific plan, principal, scope, capability, boundary, and validity interval. The morphism is not required to be a single deterministic function; it may be a relation, a partial-order semantics, a bounded search, a proof-producing constructor, or a supervised physical process. What is required is that the governing law and its exclusions remain recoverable.

The full operational expansion used in the thesis is:

\\\[ O \\rightarrow \\operatorname{parse} \\rightarrow \\operatorname{route} \\rightarrow \\operatorname{admit/refuse} \\rightarrow \\operatorname{diagnose/repair} \\rightarrow \\operatorname{plan} \\rightarrow \\operatorname{authorize} \\rightarrow \\operatorname{actuate} \\rightarrow \\operatorname{receipt} \\rightarrow \\operatorname{replay}. \\\]

A domain may collapse adjacent implementation stages when the distinction has no effect on standing, but it may not erase a boundary that changes authority, semantics, or replayability.

### Rust Typestate Projection

The executable projection uses an owned `Stage<T, S>`. The marker state `S` determines which methods exist. For this topic, the Actuator trait is callable only on Stage\<AuthorizedPayload\<...\>, Authorized\>. Consuming transitions prevent the same authority-bearing value from being reused after it has crossed a boundary. The Rust layer therefore acts as a receipt-bearing call protocol, while domain-specific proof systems remain responsible for stronger mathematical claims.

```rust
let admitted = observe(value).admit(&admission_law)?;
let diagnosed = admitted.diagnose(&diagnoser)?;
let planned = diagnosed.plan(&planner)?;
let authorized = planned.authorize(&authorizer)?;
let actuated = authorized.actuate(&mut actuator)?;
let receipted = actuated.receipt(&receipt_law);
let replayed = receipted.replay(&replayer)?;
```

There is intentionally no `actuate` method on `Stage<_, Planned>`. The absence is the compile-time form of the broker-only DO path.

### Evidence

Evidence appropriate to this section includes authorization envelopes, broker logs, deterministic patches, negative capability tests, and decisive acceptance tests. A sufficient receipt is an actuation receipt binding the authorized intent to the observed machine-state consequence. Evidence is evaluated by the verification ladder: unit, integration, end-to-end, chaos, stress, benchmark, and verifier report. Not every topic requires every rung, but skipped rungs are recorded rather than implied.

### Exclusions

This section does not claim that a common equation makes all domains identical. It does not replace native semantics, human judgment, theology, planning theory, or proof kernels with Rust types. It does not infer universal authority from local success. It asserts that the same necessary law-state distinctions remain recoverable across the examined domain.

### Falsifier

A decisive falsifier would preserve the native objects and demonstrate a consequence with recognized standing while no equivalent observation, admission boundary, lawful transformation, artifact, or receipt can be recovered. The counterexample must use the same domain objects and recognition conditions; adjacency or renamed vocabulary is insufficient. For 19.6 Zero Unreceipted Actuation, the practical test is to construct two cases identical at the admitted boundary and under the same law, yet carrying incompatible standing without any differing receipt or authority condition.

### Operationalization

Operationally, 19.6 Zero Unreceipted Actuation is implemented by declaring the boundary, encoding the transition law, producing the artifact, recording the receipt, and replaying the result. Failures return typed constructors rather than ambiguous booleans. The intended result is a system that can say not only what it produced, but why that production had standing and how another verifier can challenge it.

### Research Anchors

Primary anchors for this section include capability-security literature; policy decision and enforcement point architectures. The bibliography records the edition or publication used by the thesis.

## Chateco operationalization

For this research object, the relevant Chateco surfaces are **BRCE, CASTLE, receipt/replay rails**. They are not interchangeable. The composition root names identity and relationships; owning repositories provide implementation behavior; formal rails prove only propositions encoded inside their own logic; runtime rails establish only behavior actually executed; and receipts bind those observations to the exact subject. A defensible implementation therefore preserves the correspondence

\[
\text{graph} \rightarrow \text{query} \rightarrow \text{ggen} \rightarrow \text{formal admission} \rightarrow \text{runtime} \rightarrow \text{BRCE} \rightarrow \text{receipt} \rightarrow \text{replay}.
\]

Any skipped edge must be reported as `UNKNOWN`, `BLOCKED`, `UNSUPPORTED`, or a typed refusal rather than silently inferred. The operational target is not maximal execution. It is maximal *reversible lawful construction* followed by the narrowest authorized consequential transition.

## Exclusions

This chapter does **not** infer universal truth from one implementation, formal correctness from compilation, production authority from credentials, successful execution from workflow existence, or class closure from one solved instance. It does not treat a public ontology as automatically legitimate, a proof kernel as a sensor of external reality, or a receipt-shaped record as sufficient when exact identity and consequence are missing.

## Falsifier

A refutation must preserve the same native objects and recognition boundary. The chapter is falsified if a competing system can obtain the same recognized standing while no equivalent admission boundary, lawful transformation, authority condition, consequential actuation boundary, or receipt/replay relation can be recovered. A merely adjacent mechanism, renamed vocabulary, or different definition of success is evidence of another design, not yet a refutation.

## Research receipt

Advancement beyond conceptual standing requires an exact subject SHA or digest, admitted inputs, the verifier and toolchain identity, the command or protocol actually executed, exit/result evidence, negative fixtures where applicable, persisted receipt material, and deterministic or semantically equivalent replay. Until those obligations are satisfied for the exact subject, the correct status remains bounded rather than crowned.
