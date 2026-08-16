# 62. Axiomatic Kernel and Type Discipline

This chapter isolates a compact axiom system from which the operational architecture can be reconstructed. The purpose is not to claim mathematical completeness in the metatheoretic sense. The purpose is to make hidden assumptions explicit enough that implementations can be tested against them.

## 62.1 Primitive sorts

Let the constitutional universe contain disjoint sorts:

\[
\mathcal U = O \sqcup O^* \sqcup C \sqcup E \sqcup A^* \sqcup A_c^* \sqcup A \sqcup R \sqcup F.
\]

Interpretation:

- \(O\): observations without admitted standing;
- \(O^*\): admitted observations/semantic states;
- \(C\): constructed candidates;
- \(E\): evidence objects;
- \(A^*\): verified intents or candidate actions;
- \(A_c^*\): consequential intents admitted under authority;
- \(A\): consequences/artifacts with standing appropriate to their class;
- \(R\): receipts;
- \(F\): typed refusals.

The coproduct symbol is intentional: the constitution rejects silent coercions among these sorts.

## 62.2 Partial morphisms

The primary morphisms are partial because refusal is lawful:

\[
\alpha_e:O\rightharpoonup O^*\sqcup F,
\]

\[
\mu:O^*\times\Xi\rightharpoonup C\sqcup F,
\]

\[
\nu:C\rightharpoonup (A^*\times E)\sqcup F,
\]

\[
\beta_o:A^*\times\Theta\rightharpoonup A_c^*\sqcup F,
\]

\[
\operatorname{BRCE}:A_c^*\rightharpoonup (A\times R_a)\sqcup F.
\]

Here \(\Theta\) carries authority/policy state and \(\Xi\) carries construction context. They are factored so that \(O^*\) is not passed twice under two names.

## 62.3 Axioms

### Axiom A1 — No ambient coercion

There is no implicit total map

\[
O\to O^*,\quad C\to A,\quad A^*\to A,
\]

or other coercion that crosses a constitutional boundary.

### Axiom A2 — Generated does not imply admitted

For any projection or generator \(g\),

\[
g(x)=y \not\Rightarrow y\in O^* \text{ or } y\in A_c^*.
\]

Generation is a construction fact, not an authority fact.

### Axiom A3 — Consequence requires operational admission

For every consequential \(a\in A\), there exists an admitted consequential intent \(a_c^*\in A_c^*\) such that BRCE produced \(a\).

\[
\forall a\in A_{conseq},\; \exists a_c^*,r:\operatorname{BRCE}(a_c^*)=(a,r).
\]

### Axiom A4 — Consequence is receipted

No successful consequential return type omits a receipt:

\[
\operatorname{codom}(\operatorname{BRCE})\subseteq (A\times R_a)\sqcup F.
\]

### Axiom A5 — Receipt identity binds subject

A receipt contains or commits to enough identity material to distinguish the exact subject of execution. Abstractly,

\[
\iota:R\rightarrow \mathcal I,
\]

where \(\mathcal I\) contains immutable identity such as exact content digests, revisions, policy versions, capability identity, and temporal context.

### Axiom A6 — Refusal is terminal for the attempted transition

If a boundary returns \(f\in F\), no success consequence for that same transition may be inferred from the refusal object.

### Axiom A7 — Replay is observation, not authority

A replayed trace may reconstruct or test a consequence, but replay output acquires no greater authority than the replay environment grants.

### Axiom A8 — Representation is subordinate to semantic correspondence

For each projection \(\pi_i\), representational standing requires correspondence to admitted semantic state under an explicit contract \(K_i\):

\[
K_i(O^*,\pi_i(O^*))=\top.
\]

### Axiom A9 — Class standing requires transfer

Instance success does not imply class closure. Class standing requires at least one admitted transfer witness to a distinct member of the class.

### Axiom A10 — Standing is scoped

`ALIVE` is not a universal predicate. It is parameterized by subject, boundary, verifier, context, and time:

\[
ALIVE(s,b,v,c,t).
\]

## 62.4 Derived propositions

### Proposition P1 — Planner substitution invariance

If planners communicate only through the candidate interface and possess no direct BRCE capability, replacing planner \(p_1\) with \(p_2\) does not expand operational authority.

**Sketch.** Operational authority is determined by reachability from admitted consequential intent to BRCE, not by the internal search algorithm. If both planners terminate at \(C\) or \(A^*\), their substitution changes candidate distribution but not the authority graph. ∎

### Proposition P2 — Documentation cannot self-promote release standing

If documentation is a projection \(\pi_d(O^*)\), then a statement inside the document that a release is `ALIVE` cannot itself establish the required standing unless the release verifier independently admits it.

This follows from A2, A8, and A10.

### Proposition P3 — Receipt omission is a type error

Under A4, any successful consequential implementation path returning only \(A\) is not merely under-instrumented; it is constitutionally ill-typed.

## 62.5 Model boundary

The axioms do not guarantee that observations are true, policies are wise, verifiers are bug-free, or cryptography is perfect. They guarantee something narrower and more useful: **those uncertainties remain represented as separate obligations rather than being erased by architecture.**