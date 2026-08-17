# 16. Theorem-Carrying Construction

When generation is cheap, the highest-leverage artifact is often not the generated program but the generated program **plus the obligations that explain why it may advance**.

This is theorem-carrying construction.

## Construction emits obligations

Instead of generating an infrastructure plan and then asking humans to remember what must be checked, the manufacturing function can emit a candidate together with explicit proof obligations:

\[
\mu(O^*) = (A, \{\phi_1,\phi_2,\ldots,\phi_n\})
\]

Examples include:

- no public ingress exists;
- data residency remains inside an admitted jurisdiction;
- every mutable artifact has provenance;
- cost remains below a bound;
- an authority path contains the required broker;
- a migration preserves a schema invariant;
- an interface projection preserves capability semantics.

Some obligations are decidable statically. Others require formal proof, simulation, or runtime evidence.

## Proof does not grant DO

Even a fully discharged theorem set does not create operational authority.

That distinction is critical. Formal admissibility answers “is this construction consistent with the encoded law?” Operational admission answers “may this exact subject be actuated now by this authority?”

The two questions are related but not identical.

## Proof artifacts need identity

A theorem should bind to the definitions, source identities, generated artifact, and toolchain assumptions it actually proves.

If the artifact changes, the proof cannot be casually reused unless equivalence is established.

This is the formal analogue of exact-head verification.

## Generated proofs require independent kernels

A post-AGI model may generate Lean terms extremely effectively. That does not weaken formal assurance if the trusted kernel remains small and independently checks the term.

The architecture should exploit intelligence to construct proof candidates while preserving a minimal verifier whose acceptance rules are not controlled by the candidate.

## From tests to proof obligations

Not every test should become a theorem. Empirical behavior, performance, external APIs, and physical effects often remain runtime concerns.

The value is in classifying obligations correctly:

\[
Invariant = Formal \cup Semantic \cup Empirical \cup Operational
\]

Each class receives the narrowest adequate verifier.

## Falsifier

A theorem-carrying artifact is unsound if its proof can remain “valid” after the exact definitions or artifact it refers to have changed without an equivalence proof.

## Operational exercise

Take one ggen pack and list the propositions that must hold for its output to advance. Separate those propositions into SHACL, type-level, Lean-level, GymAct, and runtime postcondition obligations. The result is the beginning of a theorem-carrying manufacturing contract.