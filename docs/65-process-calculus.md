# 65. Process Calculus: When the Process Is Its State

Traditional workflow systems often separate a process definition, an execution-state database, an event log, and an analytics store. That decomposition is convenient, but it creates synchronization obligations among representations that describe one evolving process.

The Chatman Ecosystem explores a stronger thesis:

> **For suitably event-complete workflows, the process history can be the authoritative state carrier, and current state can be derived as a lawful projection of that history.**

## 65.1 Event-complete state

Let an object-centric event log be

\[
L_t = \langle e_1,e_2,\ldots,e_t\rangle.
\]

Define a deterministic state fold

\[
\Phi:L_t\rightarrow S_t.
\]

If every state-relevant transition is represented in the log and the fold is deterministic, then a separate mutable workflow-state store is not logically necessary for semantic state:

\[
S_t=\Phi(L_t).
\]

Caches and indexes may still exist for performance; they are projections, not independent truth.

## 65.2 Object-centric semantics

A process rarely concerns one case identifier. OCEL-style events may relate to multiple objects:

\[
e=(activity,time,\{o_1,\ldots,o_k\},attributes).
\]

This is important for enterprise work where one event may connect a customer, contract, service, deployment, incident, asset, and approval.

The semantic state is therefore a graph-valued fold rather than a scalar case-state machine.

## 65.3 POWL and partial orders

Rigid total-order workflows over-specify concurrency. Let a process execution be a partially ordered set

\[
P=(E,\preceq),
\]

where \(e_i\preceq e_j\) means \(e_i\) must precede \(e_j\), while incomparable events may proceed independently subject to resource and authority constraints.

This provides a natural interface to DfCM: construct many lawful linearizations or concurrent schedules without pretending the specification selected one total order prematurely.

## 65.4 State transition law

For each admitted event \(e_t^*\),

\[
S_{t+1}=\delta(S_t,e_t^*).
\]

But if the event itself is consequential, its admission must already be bound to a receipt. A stronger event record is therefore

\[
\hat e_t=(e_t,R_t,subject_t,policy_t).
\]

The process history becomes a causally richer state carrier.

## 65.5 Replay theorem schema

Assume:

1. deterministic fold \(\Phi\);
2. immutable ordered event identities;
3. deterministic interpretation of referenced policies and schemas;
4. complete capture of state-relevant events.

Then replay determinism requires

\[
\Phi(L_t)=\Phi(replay(L_t)).
\]

A violation identifies either nondeterministic state derivation, missing event semantics, mutable external dependencies, or identity drift.

## 65.6 Why this matters at very low latency

Every independently writable representation introduces a coherence problem. If workflow state, process log, and operational graph are separately mutable, then correctness requires maintaining a relation such as

\[
S_t \simeq \Phi(L_t) \simeq Q(G_t).
\]

At high actuation rates, synchronization itself becomes work. Collapsing semantic state onto one receipted event substrate removes one class of coherence transitions. Materialized views may be regenerated or incrementally maintained without acquiring canonical authority.

## 65.7 Refusal semantics

A refused transition should be representable without falsifying process state. One option is to record a refusal event

\[
f_t=(attempt,reason,evidence,policy)
\]

that changes diagnostic history but not the prohibited domain state.

Thus

\[
\delta_{domain}(S_t,f_t)=S_t,
\]

while

\[
\delta_{audit}(H_t,f_t)=H_{t+1}.
\]

This distinction preserves observability without pretending a refused actuation occurred.

## 65.8 Empirical test

Compare two implementations of the same workflow:

- **separated state:** mutable workflow DB + event log + analytics graph;
- **process-as-state:** receipted event substrate + derived views.

Measure:

- semantic drift incidents;
- number of reconciliation mechanisms;
- end-to-end latency;
- replay fidelity;
- storage amplification;
- recovery complexity;
- number of independent mutable truths.

The thesis stands only if the process-as-state architecture reduces coherence burden without unacceptable performance or availability cost.