# 67. Authority, Reachability, and Security Theorem Schemas

The ecosystem’s security model is structural: authority is represented as reachability to consequential transitions. Security then becomes, in part, a proof that forbidden principals or components cannot reach protected consequences.

## 67.1 Authority graph

Let

\[
G_A=(V,E_A)
\]

be a directed capability graph. Vertices include principals, services, tokens, policies, constructors, verifiers, actuators, resources, and receipt sinks. An edge \(u\to v\) means \(u\) can lawfully invoke, delegate to, or otherwise cause \(v\) under specified conditions.

For principal \(p\), define authority closure

\[
Reach(p)=\{v\in V\mid p\leadsto v\}.
\]

A protected consequence \(q\) is unavailable to \(p\) when

\[
q\notin Reach(p).
\]

## 67.2 The non-reachability theorem schema

Let \(U\subseteq V\) be untrusted components and \(D\subseteq V\) consequential `DO` vertices. Suppose every path from \(U\) to \(D\) crosses an operational admission cut \(K\), and no member of \(U\) can modify \(K\), its policy inputs, or its trusted evidence roots.

Then compromise of \(U\) alone is insufficient to reach \(D\).

Formally, if

\[
\forall u\in U,d\in D,\; Paths(u,d)\subseteq PathsThrough(K),
\]

and the adversary lacks write reachability to \(K\)’s admission basis, then

\[
Compromise(U)\not\Rightarrow Reach(D).
\]

This is a theorem schema because an implementation must instantiate the graph and prove the premises.

## 67.3 Receipt completeness as postcondition

For each consequential transition \(d\), require

\[
Post(d)\Rightarrow \exists r\in R_a: binds(r,d,subject,policy,result).
\]

A missing receipt is therefore either:

1. evidence that the actuation path violated the constitution;
2. evidence loss;
3. a false claim that the consequence occurred.

All three are operationally significant.

## 67.4 Confused deputy resistance

A common failure occurs when a low-authority component can induce a high-authority component to act outside the intended subject. Prevent this by binding capability to subject and intent:

\[
cap=(principal,operation,subject,scope,expiry,policy).
\]

BRCE admits only when the candidate intent unifies with the capability tuple.

A generic “deploy” capability without subject binding increases ambient authority; a capability for exact subject \(s\) under exact policy \(p\) is narrower.

## 67.5 Synthetic worlds and provenance

Simulation and replay are powerful precisely because downstream systems can be tested against realistic process worlds. But provenance must distinguish constructed observations from production observations.

Let

\[
origin(o)\in\{synthetic,replay,production\}
\]

be committed in trusted provenance. Cryptographic identity can make origin tamper-evident, but cryptography cannot make a synthetic event become a production event. The semantic distinction must remain explicit.

This protects both directions:

- synthetic data cannot silently acquire production standing;
- downstream services can be tested on production-shaped data without acquiring production authority.

## 67.6 Air-gap theorem schema

Consider a constructed cloud/service simulator \(S\) and a production actuator \(P\). If there exists no authority path from \(S\)’s execution principal to \(P\)’s consequential capabilities,

\[
P\notin Reach(S),
\]

then arbitrary behavior inside \(S\) cannot directly actuate \(P\) through the modeled capability graph.

This is stronger than asking the simulated agent to “behave safely.”

## 67.7 Security metric

Traditional vulnerability counts can reward shallow scanning. A more architectural metric is protected bad-outcome reachability:

\[
\rho = \frac{|Bad\cap Reach(U)|}{|Bad|}.
\]

The target is \(\rho=0\) for declared untrusted sets under declared capability assumptions.

A second metric is minimum cut cost:

\[
\kappa(U,Bad)=\min_{K}\sum_{e\in K}cost(e),
\]

where removing \(K\) disconnects \(U\) from `Bad`. Increasing \(\kappa\) may indicate stronger defense in depth, while eliminating accidental paths reduces attack surface.

## 67.8 Security falsifier

The security thesis is falsified at a scoped boundary by any reproducible path in which an untrusted constructor, planner, model, or replay environment causes a protected consequential transition without satisfying operational admission and producing a valid receipt.

That is a crisp experimental target. It converts “agent safety” from behavioral hope into graph reachability plus runtime evidence.