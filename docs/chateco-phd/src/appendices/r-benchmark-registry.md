# Appendix R — Benchmark Registry

This appendix is a reference surface for the Chateco doctoral program. Its source correspondence is **8.6 Benchmark Verification**.

This section establishes **8.6 Benchmark Verification** as a distinct law-state problem inside runtime, WASM, OTP, build, and release systems. Its native objects are processes, modules, supervisors, messages, builds, packages, traces, benchmarks, and release artifacts. The analysis preserves those objects before mapping them to the Chatman Equation; the equation is not allowed to erase domain structure merely to obtain a verbal match.

The central proposition is that 8.6 Benchmark Verification receives standing only when the relevant observation is admitted, the transformation is lawful for the declared boundary, and the consequence is connected to a receipt. In this domain, manufacture includes compilation, invocation, supervision, restart, deployment, benchmarking, tracing, and release.

### Preserve

The preserved domain includes processes, modules, supervisors, messages, builds, packages, traces, benchmarks, and release artifacts. Each object retains its own identity, lifecycle, authority, and failure conditions. A mapping is admissible only when it preserves the native distinction between what exists, what is observed, what is authorized, what changes, and what the institution or verifier recognizes afterward.

The strongest live claim is retained: the artifact need not be a file. It may be a graph, proof, plan, capability, changed relationship, deployed resource, or physical event. The invariant concerns the lawful production of consequence, not a preferred substrate.

### Fence

The boundary for this section excludes semantic inflation. A recognized token is not necessarily a supported feature. A generated string is not necessarily a proof. A completed physical movement is not necessarily authorized. A log line is not necessarily an adequate receipt. The domain-specific failure to avoid is that an executable runs but its version, configuration, authority, or result cannot be reconstructed.

Claims are classified as demonstrated, inferred, proposed, unknown, or unsupported. `UNKNOWN` is not promoted into `ADMITTED`; `UNSUPPORTED` is not rewritten as a refusal of the underlying proposition. These distinctions are part of the result rather than editorial caution added afterward.

### Calculus

The local projection is written as

\\\[ O \\xrightarrow{\\operatorname{admit}} O\^\* \\xrightarrow{\\mu} A \\xrightarrow{\\operatorname{receipt}} R. \\\]

Here, admission means a versioned executable environment and capability witness bounded by policy and resource limits. The morphism is not required to be a single deterministic function; it may be a relation, a partial-order semantics, a bounded search, a proof-producing constructor, or a supervised physical process. What is required is that the governing law and its exclusions remain recoverable.

The full operational expansion used in the thesis is:

\\\[ O \\rightarrow \\operatorname{parse} \\rightarrow \\operatorname{route} \\rightarrow \\operatorname{admit/refuse} \\rightarrow \\operatorname{diagnose/repair} \\rightarrow \\operatorname{plan} \\rightarrow \\operatorname{authorize} \\rightarrow \\operatorname{actuate} \\rightarrow \\operatorname{receipt} \\rightarrow \\operatorname{replay}. \\\]

A domain may collapse adjacent implementation stages when the distinction has no effect on standing, but it may not erase a boundary that changes authority, semantics, or replayability.

### Rust Typestate Projection

The executable projection uses an owned `Stage<T, S>`. The marker state `S` determines which methods exist. For this topic, the runtime adapter receives only Authorized values and returns Actuated artifacts or typed failures. Consuming transitions prevent the same authority-bearing value from being reused after it has crossed a boundary. The Rust layer therefore acts as a receipt-bearing call protocol, while domain-specific proof systems remain responsible for stronger mathematical claims.

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

Evidence appropriate to this section includes strict-mode fixtures, compatibility tests, traces, benchmarks, and release-law checks. A sufficient receipt is content hashes, event logs, build records, benchmark outputs, and release provenance. Evidence is evaluated by the verification ladder: unit, integration, end-to-end, chaos, stress, benchmark, and verifier report. Not every topic requires every rung, but skipped rungs are recorded rather than implied.

### Exclusions

This section does not claim that a common equation makes all domains identical. It does not replace native semantics, human judgment, theology, planning theory, or proof kernels with Rust types. It does not infer universal authority from local success. It asserts that the same necessary law-state distinctions remain recoverable across the examined domain.

### Falsifier

A decisive falsifier would preserve the native objects and demonstrate a consequence with recognized standing while no equivalent observation, admission boundary, lawful transformation, artifact, or receipt can be recovered. The counterexample must use the same domain objects and recognition conditions; adjacency or renamed vocabulary is insufficient. For 8.6 Benchmark Verification, the practical test is to construct two cases identical at the admitted boundary and under the same law, yet carrying incompatible standing without any differing receipt or authority condition.

### Operationalization

Operationally, 8.6 Benchmark Verification is implemented by declaring the boundary, encoding the transition law, producing the artifact, recording the receipt, and replaying the result. Failures return typed constructors rather than ambiguous booleans. The intended result is a system that can say not only what it produced, but why that production had standing and how another verifier can challenge it.

### Research Anchors

Primary anchors for this section include WebAssembly specification; Erlang/OTP design principles; BLAKE3 specification. The bibliography records the edition or publication used by the thesis.

## Standing rule

Entries in this appendix are descriptive until bound to exact repository, ref/SHA or artifact digest, owning verifier, and receipt/replay evidence. Registry membership is not operational standing.
