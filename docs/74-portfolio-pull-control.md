# 74. Portfolio Pull Control Across Hundreds of Repositories

When the production surface reaches hundreds of repositories, repo selection itself becomes a scheduling problem. If a human chooses the next repository primarily from memory, recency, or visible annoyance, the portfolio remains manually operated even if each local task is heavily automated.

## 74.1 Repositories as production cells

Let the eligible portfolio be

\[
\mathcal R_t=\{r_1,\ldots,r_n\}.
\]

For each repository maintain observable state

\[
X(r)=\big(S,W,B,D,A,V,P\big)
\]

where \(S\) is standing, \(W\) WIP, \(B\) blockers, \(D\) dependencies, \(A\) age, \(V\) expected value, and \(P\) next lawful production actions.

The portfolio scheduler consumes \(X(r)\); it should not require a human to reconstruct it conversationally.

## 74.2 Kanban as graph token

A software kanban is not merely a card on a board. It is a typed demand token emitted by a state transition.

Examples:

- downstream dependency requires regeneration;
- verifier becomes available;
- capability-blocked POC becomes feasible;
- release closure requires exact evidence;
- CI failure creates bounded repair demand;
- ontology change invalidates projections.

Formally,

\[
K=(subject,reason,required\_standing,authority,cost,expiry).
\]

A kanban has no ambient DO authority; it is demand for lawful manufacture.

## 74.3 Priority is a policy, not intuition

Define a scheduling score

\[
\Pi(r)=f(V,dependency\_centrality,WIP\_age,closure\_probability,recovery\_leverage,cost,risk).
\]

The exact function is policy and can change. What matters constitutionally is that inputs and policy are explicit, replayable, and separable from execution authority.

## 74.4 Dependency pull

Suppose an admitted change to canonical source \(s\) affects repositories

\[
A(s)=\{r\in\mathcal R:depends(r,s)\}.
\]

The graph should manufacture downstream demand automatically:

\[
\Delta s
\rightarrow
A(s)
\rightarrow
\{K_r:r\in A(s)\}
\rightarrow
\text{rebuild/verify/receipt}.
\]

No operator should have to remember the fanout set.

## 74.5 WIP pull

Long-lived WIP also generates demand. Let \(age(w)\) be age of a WIP object and \(b(w)\) its blocker state. A closure governor can raise work when

\[
age(w)>\tau
\quad\land\quad
b(w)\in\text{currently solvable classes}.
\]

This converts Little's Law from reporting into control.

## 74.6 Pull does not mean low throughput

TPS pull is often misread as “do less.” The correct interpretation is “produce because the system has a real demand signal rather than because upstream capacity can make inventory.”

If the graph contains thousands of valid demand tokens, high throughput is entirely consistent with pull.

Thus

\[
\text{pull}\not\Rightarrow\text{slow}.
\]

Instead,

\[
\text{pull}\Rightarrow\text{demand-coupled production}.
\]

## 74.7 Portfolio WIP ceiling

A WIP ceiling can still be useful at specific constrained service centers. It should protect flow at the bottleneck, not become a global prohibition on creating independently closable value.

Use local bounds

\[
WIP_k\le B_k
\]

for service center \(k\), while allowing unrelated cells to continue when their closure paths are independent.

## 74.8 Operator removal criterion

The portfolio is no longer manually scheduled when the ordinary next-work set can be derived as

\[
N_t=query(G_t,policy_t)
\]

and executed through lawful manufacturing without the operator naming repositories one by one.

Human intervention remains for changing policy, introducing novel goals, resolving irreducible ambiguity, and accepting explicitly human-held authority.

## 74.9 Portfolio acceptance test

A Fortune-5-scale portfolio controller should demonstrate:

1. discovery of the full eligible repository set;
2. exact-head identity for every scheduled subject;
3. dependency graph reconstruction;
4. WIP state and age reconstruction;
5. dormant-POC classification;
6. deterministic priority calculation;
7. bounded action manufacture;
8. typed refusal for unresolved blockers;
9. independent verification;
10. receipt DAG linking every closure.

The target is not a dashboard showing hundreds of repos. It is a graph that can pull the next lawful work from them.