# 9. The Algebra of Refusal

> **Program relation.** This chapter is part of the Chateco doctoral program. It preserves the native research object before mapping it into the constitutional manufacturing calculus. The preserved source anchor for this chapter is **16.12 Typed Refusals and Gall States** from the doctoral thesis corpus. It is evidence-bearing source material for the chapter, not an assertion that the chapter title and source heading are definitionally equivalent.

## Research claim

**The Algebra of Refusal** is treated here as a law-state problem rather than a slogan. The chapter asks which observations are admissible, which transformations are lawful, what authority is required for consequence, which receipts establish standing, and what replay or transfer would be required to keep that standing over time. The Chateco position is deliberately bounded: adjacency is not equivalence, execution is not proof, and absence of evidence does not become refusal by narration.

## Preserved source development

The crate distinguishes semantic and operational failure states:

```rust
pub enum RefusalKind {
    Refused,
    Unknown,
    Unsupported,
    Blocked,
    BuildBroken,
}
```

`Unknown` means the observation or evidence is insufficient to admit the claim. `Unsupported` means the implementation does not provide the requested capability. `Blocked` means a known dependency prevents progress. `BuildBroken` means the construction surface itself does not currently compile or assemble. `Refused` means the law evaluated the request and denied it.

These are not interchangeable. Treating unsupported as false corrupts semantics. Treating unknown as admitted creates fabricated certainty. Treating a broken build as a domain counterexample mistakes implementation status for theory. The runtime Gall status is recorded alongside the typestate protocol so that a stage can be operationally classified without weakening compile-time transition law.

## Chateco operationalization

For this research object, the relevant Chateco surfaces are **chatman-ecosystem composition root, ggen semantic manufacture, BRCE receipts**. They are not interchangeable. The composition root names identity and relationships; owning repositories provide implementation behavior; formal rails prove only propositions encoded inside their own logic; runtime rails establish only behavior actually executed; and receipts bind those observations to the exact subject. A defensible implementation therefore preserves the correspondence

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
