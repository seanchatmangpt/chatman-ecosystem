# 66. DfCM Search Geometry and Reversible Intelligence

DfCM—Deterministic/Design-for-Combinatorial-Maximalism in the ecosystem’s usage—treats search as the preservation of lawful reversible possibility before irreversible selection. Its central optimization target is not “fewest candidates.” It is **maximum useful option value under bounded construction cost and authority constraints**.

## 66.1 Candidate space

Let \(X\) be the syntactic candidate universe. Constitutional constraints induce an admitted construction region

\[
\mathcal C = \{x\in X\mid Ontology(x)\wedge Capability(x)\wedge Policy(x)\wedge Cost(x)\le B\}.
\]

DfCM attempts to construct a broad subset \(C\subseteq\mathcal C\) before selection.

The crucial distinction is

\[
CONSTRUCT(C)\neq SELECT(c^*)\neq DO(c^*).
\]

Search breadth therefore does not imply authority breadth.

## 66.2 Reversibility order

Define a preorder \(\preceq_r\) where

\[
x\preceq_r y
\]

means choosing \(x\) preserves at least as many future lawful options as choosing \(y\). Early search should prefer moves high in reversibility unless evidence justifies commitment.

This is analogous to maintaining real options in decision theory, but here the option set is explicitly constrained by ontology and authority.

## 66.3 Information gain per irreversible bit

Let \(H(C)\) be uncertainty over candidates and let \(I(a;C)\) be information gained by reversible action \(a\). Define an exploratory score

\[
J(a)=\frac{I(a;C)}{Cost(a)+\lambda Irrev(a)}.
\]

A DfCM policy can favor actions that increase discriminative evidence while spending little irreversible authority.

This formalizes a practical engineering instinct: compile, simulate, query, replay, model-check, or generate before deploying.

## 66.4 Topology, not failure

If one candidate edge fails a constraint, DfCM removes or annotates that edge rather than declaring the entire search graph invalid.

For graph \(G=(V,E)\), refusal of edge \(e\) yields

\[
G'=(V,E\setminus\{e\})
\]

or a typed edge annotation, not necessarily \(G'=\varnothing\).

This matters in infrastructure, planning, migration, scheduling, and adversarial modeling where large portions of the solution space may remain lawful after one failure.

## 66.5 Perfect information as a limiting case

When the system has complete modeled state for itself and an adversary, search resembles a perfect-information game. Let state \(s\), lawful action set \(A(s)\), adversarial responses \(B(s,a)\), and terminal utility \(U\). Then a minimax-style value may be written

\[
V(s)=\max_{a\in A(s)}\min_{b\in B(s,a)}V(T(s,a,b)).
\]

DfCM adds a constitutional restriction: neither exploration nor opponent modeling grants direct actuation. Search may be exhaustive while `DO` remains narrow.

## 66.6 Goal-first adversarial modeling

A vulnerability model need not start from known exploits. It may start from an adversarial goal \(g\) and search backward over lawful or hypothesized state transitions:

\[
Pred(g)=\{s\mid \exists p:s\leadsto g\}.
\]

For defensive use, the system can compute cut sets \(K\) such that removing or refusing transitions in \(K\) disconnects initial states from protected bad outcomes:

\[
Init \not\leadsto Bad \quad\text{in } G\setminus K.
\]

This turns security architecture into reachability reduction rather than a catalog of anecdotes.

## 66.7 Search completeness versus practical boundedness

Absolute combinatorial completeness is usually impossible. The correct claim is bounded completeness relative to declared limits:

\[
Complete(Ontology,Capabilities,Bounds,Time,Cost).
\]

A receipt should preserve those bounds. Without them, “we explored all possibilities” is not a falsifiable statement.

## 66.8 DfCM benchmark

For a benchmark family, compare:

- single-plan generation;
- beam search;
- stochastic agent search;
- DfCM bounded lawful expansion.

Measure:

- admitted solution coverage;
- best-solution quality;
- irreversible actions during search;
- verifier calls;
- cost;
- recovery after injected failures;
- transfer to topology variants.

The central hypothesis is not that DfCM always wins on raw speed. It is that **reversible breadth plus strict actuation separation improves robust closure when environments are complex, adversarial, or partially failing.**