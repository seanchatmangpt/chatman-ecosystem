# 73. The Latent POC Reservoir and the Moving Capability Frontier

A large repository portfolio contains more than maintained products. It may contain experiments that were stopped because the problem was false, because priorities changed, because dependencies failed, or because the available models and tools could not complete the work at the time.

Treating all unfinished POCs as equivalent technical debt destroys information.

## 73.1 Typed dormant-state classification

For dormant repository \(r\), define

\[
D(r)\in\{FALSIFIED,OBSOLETE,DEPENDENCY\_BLOCKED,TOOLCHAIN\_BLOCKED,CAPABILITY\_BLOCKED,VIABLE,UNKNOWN\}.
\]

Only the first two classes should be presumed dead. The remaining classes encode option value.

## 73.2 Capability-blocked work

Let \(C_t\) be available manufacturing capability at time \(t\), and let \(q(r)\) be the minimum capability required to close repository \(r\). A capability-blocked project satisfies

\[
C_t<q(r).
\]

As models, generators, planners, verifiers, and toolchains improve, the frontier moves:

\[
C_{t+1}\ge C_t.
\]

A previously blocked project becomes recoverable when

\[
C_{t+k}\ge q(r).
\]

No new idea was required. Technology changed the feasibility of an already explored branch.

## 73.3 POC inventory as option portfolio

A dormant POC may already contain paid-for exploration:

- problem framing;
- architecture;
- domain ontology;
- source code;
- tests;
- fixtures;
- dependency choices;
- failed approaches;
- benchmark harnesses;
- documentation;
- known blockers.

Its marginal cost to verified standing can therefore be far lower than a greenfield equivalent.

Define recoverable option value

\[
V_r=P(close\mid C_t)\cdot U(r)-Cost_{remaining}(r),
\]

where \(U(r)\) is expected utility of closure.

## 73.4 Continuous capability re-evaluation

A manually operated portfolio revisits dormant POCs when the operator remembers them. A production system continuously asks:

\[
D_t(r)=CAPABILITY\_BLOCKED
\quad\land\quad
C_{t+1}>C_t
\Rightarrow
\text{re-evaluate }r.
\]

Model upgrades, new ggen packs, new parsers, planner additions, CI fixes, or formal tooling improvements can all trigger re-evaluation.

## 73.5 Archaeology before resurrection

Recovery does not mean blindly merging historical branches. The lawful path is

\[
\text{old artifact}
\rightarrow
\text{observe semantic delta}
\rightarrow
\text{separate valid knowledge from obsolete ancestry}
\rightarrow
\text{reconstitute on current constitution}.
\]

This is where ggen-legacy is structurally important: legacy implementation becomes observation, not authority.

## 73.6 The reservoir effect

If \(N_d\) dormant projects exist and fraction \(p_t\) become recoverable at current capability, then the newly reachable work reservoir is

\[
R_t=N_d\cdot p_t.
\]

A technology shock that increases \(p_t\) can unlock many projects at once. This creates nonlinear portfolio response to a single capability improvement.

## 73.7 Recovery throughput

Total valuable arrival rate becomes

\[
\Lambda_v=\Lambda_{new}+\Lambda_{recovered}.
\]

The recovered term is strategically important because it converts historical exploration into present production without requiring equivalent new ideation.

## 73.8 Required evidence

A recovery engine should emit, per repository:

1. exact repository and head identity;
2. historical blocker hypothesis;
3. present blocker reproduction result;
4. current dependency status;
5. nearest executable verifier;
6. required semantic migration;
7. predicted closure cost;
8. resulting typed state;
9. next lawful transition.

The system must be allowed to conclude that the old idea was wrong. Recovery is not nostalgia; it is evidence-driven re-admission.

## 73.9 Research prediction

If the moving-capability-frontier thesis is correct, periods of model/tool improvement should create measurable bursts of old-POC closure. The fraction of dormant repositories that transition from capability-blocked to viable should correlate with relevant capability improvements more strongly than with human recollection events.

That is the difference between a portfolio archive and a capability reservoir.