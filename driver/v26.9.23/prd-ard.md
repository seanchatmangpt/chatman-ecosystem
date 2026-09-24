<!-- Provenance: operator-authored prose, pasted into the Claude Code session 1fecd79a on 2026-09-22 ~23:10 PT
     with the directive "run ultracode loops overnight until v26.9.23 is complete for all of my projects".
     Status: ACCEPTED by operator testimony (O* by fiat). This file is the GC23-0 source text; it is preserved
     verbatim and is not executable authority (PR-001). Propositions are compiled from it (GC23-0 / GC23-2). -->

I’m treating this as the **canonical v26.9.23 product and architecture pair**: one finite product contract and one implementation contract. The key change from v26.9.22 is that v26.9.23 is not another “agent factory” release; it is the first release where **prose defines the bounded future, semantics become canonical, and KNOWN work is expected to leave the LLM path entirely**.

# Product Requirements Document

## Semantic Manufacturing v26.9.23

**Version:** v26.9.23
**Status:** Proposed successor to v26.9.22 / GC-FRI-0800
**Product class:** Semantic manufacturing and execution control plane
**Primary systems:** sJira, SA2A, XaaS, BRCE, GALL, OCEL, MachineExperience, ggen ecosystem
**Canonical executable source:** admitted RDF/TTL graph
**Primary design objective:** reduce repeated semantic reasoning until KNOWN work requires zero LLM participation.

---

# 1. Executive Summary

v26.9.23 turns the discoveries of v26.9.22 into a reusable operating system for creating new systems.

The core product loop is:

$$
\boxed{
Prose
\rightarrow
SemanticFuture
\rightarrow
FiniteDelta
\rightarrow
sJira
\rightarrow
SA2A
\rightarrow
XaaS/BRCE
\rightarrow
Execution
\rightarrow
Receipt
\rightarrow
OCEL
\rightarrow
MachineExperience
\rightarrow
SemanticFuture
}
$$

An LLM may help invent or interpret a future that has never existed before.

Once that future has been semantically admitted, the LLM is no longer the execution engine.

v26.9.23 therefore separates two classes of work:

### UNKNOWN

Novel semantics have not yet been formalized.

UNKNOWN may use:

* LLMs;
* humans;
* experimentation;
* search;
* simulations;
* competing candidates.

UNKNOWN execution must always be bounded by explicit cost, evidence and consequence limits.

### KNOWN

The required semantics, applicability predicates and verification conditions already exist.

KNOWN uses:

* deterministic programs;
* formal planners;
* rules;
* generators;
* constraint solvers;
* Ash/Reactor/state machines;
* validated recipes;
* deterministic capability providers.

A KNOWN path that repeatedly requires an LLM is a product defect.

---

# 2. Product Thesis

The system shall not attempt to solve arbitrary completion or arbitrary semantics problems.

Instead it shall remain outside those problem classes by construction.

## 2.1 Busy-Beaver avoidance

The system shall never define completion as:

> Continue searching until no better solution can exist.

Completion is defined from an accepted finite future-state specification.

$$
Delta_G = SemanticFuture_G - CurrentState
$$

Work stops when the propositions required by the accepted GoalCheckpoint are satisfied.

Additional improvements become successor goals.

## 2.2 Rice-theorem avoidance

The system shall not depend on inferring arbitrary semantics from arbitrary programs.

The direction is:

$$
Meaning
\rightarrow
Contract
\rightarrow
Implementation
$$

not:

$$
Program
\rightarrow
InferMeaning
$$

Generated or restricted implementations are preferred because their semantic source is already known.

Irreducible handwritten implementations require explicit contracts, observed consequences and bounded verification.

---

# 3. v26.9.22 Baseline

The v26.9.22 read-only exploration found:

* no KNOWN class currently runs end-to-end without an LLM;
* frontier→XaaS, provider resolution, deterministic execution and generic receipt promotion each contain broken edges;
* sJira lacks postcondition, capability, evidence-horizon, exclusions, consequence-class and successor-policy semantics;
* no `GoalCheckpoint` exists;
* only 13 of 85 inspected receipts conform to the current receipt schema;
* no accepted Vision/WBPR has yet been compiled into propositions;
* no prose→semantics compiler exists. 

The Friday work has already re-scoped the unbounded v26.9.22 order population so that newly discovered work enters a successor checkpoint unless it falsifies an accepted gate. 

v26.9.23 productizes this behavior.

---

# 4. Product Goal

Given a description of a previously nonexistent system in ordinary prose, v26.9.23 shall support this lifecycle:

1. Author a future-state Vision and bounded WBPR.
2. Extract candidate semantic propositions.
3. Admit those propositions into a canonical ontology.
4. Compare the admitted future to current observed state.
5. Manufacture a finite sJira work graph.
6. Resolve required capabilities through SA2A.
7. Bind execution to XaaS authority and BRCE.
8. Execute every KNOWN operation without an LLM.
9. Independently observe consequences.
10. Produce schema-valid receipts and OCEL events.
11. Derive new standing and frontier state.
12. Convert novel successful episodes into MachineExperience.
13. Route equivalent future episodes as KNOWN.
14. Stop when the accepted GoalCheckpoint is satisfied.

---

# 5. Primary Actors

## 5.1 Semantic Author

Defines an intended future through:

* Vision;
* WBPR;
* requirements prose;
* case study;
* policy;
* user testimony.

The author supplies intent, not implementation.

## 5.2 Semantic Admission System

Converts candidate meaning into admitted meaning.

Responsibilities:

* SHACL validation;
* ontology identity;
* exclusions;
* invariants;
* authority bounds;
* falsifiers;
* target postconditions.

## 5.3 sJira

Owns semantic obligations.

sJira shall be the canonical work/evidence control plane rather than a ticket UI.

Jira, Markdown, dashboards and traditional issue trackers are projections.

## 5.4 SA2A

Resolves semantic capability requirements to compatible providers.

SA2A transports intent and evidence-bound contracts.

SA2A itself has no execution authority.

## 5.5 XaaS

Owns runtime realization:

* allocation;
* provider binding;
* lease;
* resource limits;
* consequence envelope;
* execution lifecycle.

## 5.6 BRCE / CommandBus

Owns the sole lawful DO path.

There shall be zero unreceipted consequential actuation.

## 5.7 Capability Provider

May be:

* generator;
* deterministic script;
* Ash/Reactor process;
* solver;
* planner;
* database process;
* external service;
* human;
* LLM.

Provider identity is secondary to capability-contract satisfaction.

## 5.8 Independent Verifier

Observes postconditions independently of the executor's claim.

## 5.9 MachineExperience

Converts successfully resolved UNKNOWN episodes into reusable KNOWN topology.

---

# 6. Core Product Objects

v26.9.23 shall formalize the following objects.

## 6.1 Vision

Long-horizon invariants and direction.

A Vision is not itself a finite release plan.

## 6.2 WBPR

A bounded future-world description.

A WBPR shall describe what is observably true when a specific goal is complete.

## 6.3 SemanticProposition

An admitted proposition extracted from future-state prose.

Examples:

* Actor;
* State;
* Capability;
* Postcondition;
* Invariant;
* Exclusion;
* Evidence requirement;
* Falsifier;
* Authority requirement.

## 6.4 GoalCheckpoint

A finite semantic completion boundary.

Required fields:

* exact subject;
* desired state;
* required propositions;
* acceptance predicate;
* falsifiers;
* exclusions;
* evidence requirements;
* authority ceiling;
* consequence ceiling;
* replay requirement;
* successor policy.

## 6.5 WorkOrder

Required minimum tuple:

```text
WorkOrder {
  identity
  exact_subject
  current_state
  target_postcondition
  dependencies
  required_capability
  authority_ceiling
  consequence_class
  evidence_horizon
  acceptance_predicate
  falsifier
  exclusions
  successor_policy
}
```

## 6.6 Capability

A semantic contract independent of provider implementation.

## 6.7 Receipt

Required receipt dimensions:

```text
identity
authority
consequence
replay
standing
```

## 6.8 MachineExperience

An admitted reusable result derived from one or more verified episodes.

---

# 7. Functional Requirements

## PR-001 — Prose-first system definition

The system shall accept a Vision/WBPR or equivalent narrative describing a previously nonexistent system.

The original prose shall be preserved.

The prose itself shall not become executable authority.

---

## PR-002 — Prose → semantic candidate extraction

The system shall extract candidate:

* entities;
* roles;
* states;
* transitions;
* capabilities;
* triggers;
* obligations;
* dependencies;
* invariants;
* exclusions;
* evidence;
* authority;
* postconditions;
* falsifiers;
* metrics;
* successor goals.

LLM extraction is permitted because the source semantics are initially UNKNOWN.

---

## PR-003 — Semantic admission

Candidate propositions shall not become canonical merely because an LLM emitted them.

Admission shall validate:

* ontology shape;
* subject identity;
* vocabulary;
* required predicates;
* contradictions;
* exclusions;
* evidence semantics.

After admission, the RDF graph becomes canonical.

---

## PR-004 — Finite delta manufacture

The system shall compute:

$$
Delta = AcceptedFuture - AdmittedCurrentState
$$

Only the finite delta required by the active GoalCheckpoint shall become required work.

---

## PR-005 — sJira GoalCheckpoint support

sJira shall natively represent:

* GoalCheckpoint;
* parent/successor checkpoints;
* WorkOrders;
* checkpoint boundaries;
* stop queries;
* required evidence;
* exclusion semantics.

---

## PR-006 — Derived frontier

sJira shall derive frontier eligibility.

Standing shall not be an authoritative stored literal.

Changes to an exact subject covered by previous evidence shall invalidate derived standing as required.

---

## PR-007 — KNOWN/UNKNOWN separation

The system shall distinguish:

```text
UNKNOWN
PARTIAL_ALIVE
ALIVE
BLOCKED
BUILD_BROKEN
UNSUPPORTED
REFUSED(reason)
```

`UNKNOWN != ADMITTED`.

`UNSUPPORTED != REFUSED`.

`executed != verified`.

---

## PR-008 — SA2A semantic conservation

An sJira WorkOrder routed through SA2A shall preserve at minimum:

```text
subject
postcondition
required capability
authority ceiling
consequence class
evidence horizon
exclusions
```

Loss or mutation of a required semantic field shall refuse execution.

---

## PR-009 — Deterministic KNOWN execution

At least one reference WorkOrder class shall run end-to-end with:

* no LLM credentials;
* no LLM binary/provider;
* no LLM fallback;
* no conversational state.

The executor shall be a deterministic capability provider.

---

## PR-010 — Singular DO boundary

All consequential execution shall route through XaaS → BRCE/CommandBus.

Hooks may communicate intent.

Hooks shall never manufacture authority.

---

## PR-011 — Last-mile consequence

Successful command execution shall not itself satisfy a WorkOrder.

Completion requires:

* required consequence observed;
* independent postcondition verification;
* falsifier evaluation;
* receipt creation;
* OCEL observation;
* derived standing update.

---

## PR-012 — Closed frontier

A verified receipt shall re-enter admitted state.

The system shall recompute frontier eligibility.

An upstream WorkOrder completion shall deterministically:

* close itself;
* unlock eligible dependents;
* preserve ineligible dependents.

---

## PR-013 — Replay

An independent cold process shall reconstruct:

* subject identity;
* evidence;
* standing;
* completed work;
* current frontier;

from canonical artifacts without access to the original conversational transcript.

---

## PR-014 — MachineExperience ratchet

A verified UNKNOWN episode may create admitted MachineExperience.

An equivalent future episode shall route as KNOWN when the MachineExperience applicability predicate holds.

Episode 2 shall require less semantic exploration than Episode 1.

---

## PR-015 — No repeated intelligence purchase

If the system invokes an LLM repeatedly for the same admitted semantic transformation, the product shall classify the missing deterministic mechanism as a gap.

The preferred repair order is:

```text
reuse
→ compose
→ extend
→ invent
```

---

## PR-016 — Bounded UNKNOWN exploration

UNKNOWN episodes shall have explicit:

* time budget;
* compute budget;
* candidate budget;
* consequence ceiling;
* evidence requirement.

Budget exhaustion is a valid receipted terminal outcome:

```text
UNKNOWN
```

It shall not silently become success or failure.

---

## PR-017 — Stop calculus

Each active GoalCheckpoint shall expose a deterministic STOP predicate.

A goal is complete when:

1. its required postconditions are observed;
2. required dependencies have adequate standing;
3. falsifiers do not fire;
4. required receipts validate;
5. replay requirements pass;
6. no required hidden LLM/human edge remains;
7. all remaining work is typed as successor, blocked, unsupported or refused.

Newly discovered improvements shall not reopen a completed checkpoint unless they falsify an accepted proposition.

---

# 8. Bootstrap / First Mile / Core / Last Mile

## 8.1 Bootstrap

A clean process shall reconstruct:

* canonical ontology;
* current exact subjects/SHAs;
* capabilities;
* authority rules;
* evidence;
* receipts;
* active GoalCheckpoint;
* sJira frontier.

No prior chat state may be required.

### Bootstrap stop condition

Two clean independent reconstructions produce semantically identical state.

---

## 8.2 First Mile

The system shall transform:

```text
new future-state prose
→ candidate semantics
→ admitted semantics
→ finite delta
→ WorkOrders
```

### First-mile stop condition

Every required WorkOrder contains the complete semantic tuple and no executable obligation exists only in prose.

---

## 8.3 Deterministic Core

KNOWN work shall execute using the optimal existing formalism:

* HDDL/PDDL for planning;
* SAT/SMT/CP for constraints;
* SPARQL/SHACL for semantic graph operations;
* Prolog/rules for declarative inference;
* OCEL/conformance for process;
* generators for derivable software;
* Ash/Reactor/state machines for domain/runtime state.

The middle shall intentionally become boring.

---

## 8.4 Last Mile

The system shall connect execution to real consequence.

### Last-mile stop condition

```text
actuation
→ observation
→ verification
→ receipt
→ OCEL
→ derived standing
→ successor frontier
```

is closed.

---

# 9. Reference Product Flows

## 9.1 Greenfield-system flow

```text
Vision/WBPR
→ semantic extraction
→ admission
→ GoalCheckpoint
→ delta
→ sJira
→ SA2A
→ XaaS
→ deterministic implementation
→ receipt
→ replay
```

This is the primary v26.9.23 product story.

## 9.2 Western Digital FA

WD Case Study 2 remains a reference first-mile scenario.

The system shall distinguish:

```text
SUPPLIED
PUBLICLY_OBSERVABLE
ARCHITECTURAL_INFERENCE
WD_DEPENDENT_UNKNOWN
```

Internal WD facts that have not been supplied shall remain typed UNKNOWN rather than being manufactured.

## 9.3 ZOE

ZOE remains a domain application proving that the same semantic machinery can represent human-facing workflows without giving observational systems unauthorized production consequence.

## 9.4 Self-development

The Semantic Manufacturing system shall use sJira/SA2A/XaaS to express and execute its own bounded development WorkOrders where the semantics are already KNOWN.

---

# 10. Non-Goals

v26.9.23 does not require:

* solving arbitrary program semantics;
* arbitrary termination proofs;
* exhaustive improvement of every repository;
* zero UNKNOWN globally;
* replacing every handwritten implementation;
* fully autonomous production deployment;
* live WD integration;
* live Planning Center actuation;
* arbitrary agent-to-agent conversation;
* universal Claude/ZCode workflow takeover;
* merging/publishing/deploying every successor item;
* making every repository ALIVE.

---

# 11. Success Metrics

## Semantic

* 100% of required GoalCheckpoint propositions mapped to canonical semantics.
* 0 required executable obligations existing only in prose.
* 0 missing mandatory WorkOrder tuple fields.

## Execution

* ≥1 complete KNOWN episode with zero LLM participation.
* 0 unreceipted actuation.
* 0 SA2A tuple-conservation losses.

## Evidence

* 100% v26.9.23 critical-path receipts schema-valid.
* 100% critical-path standing recomputable.
* Cold replay produces identical semantic standing.

## Learning

* Episode 1 UNKNOWN → admitted MachineExperience.
* Equivalent Episode 2 routes KNOWN.
* Episode 2 uses zero semantic LLM inference.

## Completion

* STOP query returns true for the v26.9.23 GoalCheckpoint.
* Every non-required remaining item is classified.

---

# 12. v26.9.23 Product Checkpoints

### GC23-0 — Future Semantics

Accepted Vision/WBPR exists and has a complete admitted semantic projection.

### GC23-1 — Cold Bootstrap

The system reconstructs its own bounded state without chat/session context.

### GC23-2 — First-Mile Compiler

Accepted prose compiles into a finite sJira delta.

### GC23-3 — Finite Work Graph

Every required WorkOrder carries the full semantic tuple.

### GC23-4 — SA2A Conservation

Work meaning is preserved through provider resolution.

### GC23-5 — Authorized No-LLM Execution

A KNOWN WorkOrder executes with zero LLM involvement.

### GC23-6 — Consequence

Independent observation proves the required postcondition.

### GC23-7 — Receipt / OCEL

The episode produces conformant durable evidence.

### GC23-8 — Closed Frontier

The receipt changes derived sJira standing/frontier.

### GC23-9 — MachineExperience

A resolved UNKNOWN becomes a reusable KNOWN path.

### GC23-10 — Cold Replay

Independent reconstruction reaches the same standing.

### GC23-11 — Bounded Fleet

Every repo relevant to the checkpoint has exact-subject standing or an explicit non-required classification.

### GC23-12 — Semantic Self-Hosting

A new bounded improvement to this architecture can itself originate as accepted prose and enter the same pipeline without manually manufacturing a bespoke backlog.

---

# 13. Release Stop Condition

$$
STOP_{26.9.23}
=
\bigwedge_{i=0}^{12} GC23_i
$$

with:

$$
RequiredUnknown = \varnothing
$$

$$
RequiredLLM_{KNOWN} = \varnothing
$$

and:

$$
RemainingFrontier
\subseteq
Successor
\cup
Blocked
\cup
Unsupported
\cup
Refused
$$

When this predicate is true, v26.9.23 is complete.

Additional capability becomes v26.9.24+ work.

# Architecture Requirements Document

## Semantic Manufacturing v26.9.23

**Version:** v26.9.23
**Architecture style:** Ontology-first semantic manufacturing with receipted consequence
**Canonical state:** RDF/TTL + durable receipts/events
**Authority model:** BRCE singular DO path
**Execution objective:** deterministic machinery for every admitted KNOWN semantic class

---

# 1. Architectural Thesis

v26.9.23 shall implement:

$$
A=\mu(O^*)
$$

$$
R=receipt(A)
$$

where:

* \(O\) is raw observation;
* \(O^*\) is admitted, aligned, grounded and bounded observation;
* \(\mu\) is lawful manufacture;
* \(A\) is the artifact/action produced;
* \(R\) records identity, authority, consequence, replay and standing.

The recursive system is:

$$
A_t=\mu(O^*_t)
$$

$$
R_t=receipt(A_t)
$$

$$
O^*_{t+1}
=
admit(observe(World_{t+1})\cup R_t)
$$

Autonomy exists only when the receipt/consequence re-enters admitted state and changes the next frontier.

---

# 2. Top-Level Architecture

```text
                   ┌─────────────────────┐
                   │ Vision / WBPR prose │
                   └──────────┬──────────┘
                              │ UNKNOWN interpretation
                              ▼
                   ┌─────────────────────┐
                   │ Semantic Extraction │
                   └──────────┬──────────┘
                              │ candidate RDF
                              ▼
                   ┌─────────────────────┐
                   │ SHACL / Admission   │
                   └──────────┬──────────┘
                              │ O*
                              ▼
                    ┌───────────────────┐
                    │ Canonical Graph   │
                    └─────────┬─────────┘
                              │ finite delta
                              ▼
                    ┌───────────────────┐
                    │       sJira       │
                    │ Goal + Work Graph │
                    └─────────┬─────────┘
                              │ frontier
                              ▼
                    ┌───────────────────┐
                    │ Planner / Router  │
                    └─────────┬─────────┘
                              │ capability requirement
                              ▼
                    ┌───────────────────┐
                    │       SA2A        │
                    └─────────┬─────────┘
                              │ conserved contract
                              ▼
                    ┌───────────────────┐
                    │       XaaS        │
                    │ lease / provider  │
                    └─────────┬─────────┘
                              │ authority
                              ▼
                    ┌───────────────────┐
                    │ BRCE / CommandBus │
                    └─────────┬─────────┘
                              │ DO
                              ▼
                  ┌────────────────────────┐
                  │ Deterministic Provider │
                  └────────────┬───────────┘
                               │ consequence
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
           Independent                   OCEL Event
            Verifier                         │
                 │                           │
                 └─────────────┬─────────────┘
                               ▼
                         Receipt / R
                               │
                               ▼
                       Derived Standing
                               │
                               ▼
                         sJira Frontier
                               │
                               ▼
                     MachineExperience
```

---

# 3. Canonicality Rules

## AR-001

RDF/TTL is the canonical semantic graph.

## AR-002

The following are projections:

* Markdown;
* Jira issues;
* dashboards;
* WBPR rendering;
* PRD;
* ARD;
* README;
* generated code;
* compatibility APIs.

A projection shall not silently become semantic authority.

## AR-003

The prose that originates a system is preserved as provenance.

Its extracted propositions become executable only after admission.

---

# 4. Repository Responsibilities

## engineering-standards

Owns:

* global engineering doctrine;
* architectural invariants;
* semantic protocol conformance expectations;
* repository adoption contract.

It shall not become runtime state.

---

## ggen

Owns deterministic semantic manufacture.

Responsibilities:

* graph/query → generated artifact;
* portable receipt support;
* generation determinism;
* source/projection integrity;
* semantic pack execution.

---

## ggen-marketplace

Owns reusable manufacturing knowledge:

* ontology packs;
* SA2A bridge packs;
* receipt-chain packs;
* OCEL packs;
* domain-specific projections;
* semantic verification packs.

A repeated implementation pattern should move here rather than remain LLM knowledge.

---

## ggen_igniter

Owns Elixir-side semantic manufacture and sJira implementation.

Responsibilities:

* sJira ontology;
* SHACL shapes;
* GoalCheckpoint;
* WorkOrder graph;
* frontier computation;
* prose semantic candidate integration;
* semantic delta;
* XaaS descriptor manufacture;
* replay checks;
* TransitionLog.

---

## ash_a2a

Owns semantic capability typing.

Responsibilities:

* Capability;
* applicability;
* provider semantics;
* MachineExperience integration;
* KNOWN/UNKNOWN route semantics;
* zero-inference-on-KNOWN courts.

SA2A is transport/capability semantics, not authority.

---

## xaas

Owns execution realization.

Responsibilities:

* provider registry;
* resource binding;
* leases;
* authorization envelope;
* deterministic RecipeWorker;
* BRCE integration;
* court execution;
* consequence receipts;
* OCEL egress;
* stop-court execution.

---

## autofde-lab

Owns learning and qualification experiments.

Responsibilities:

* two-episode MachineExperience courts;
* failure classification;
* prior-art applicability experiments;
* POWL/PM4Py/OCEL analysis where appropriate;
* WD reference case;
* negative controls;
* semantic replay experiments.

---

## zcode-cli

Owns bounded worker CLI behavior where required.

It shall not be the semantic authority.

ZCode is an executor implementation, not the architecture.

The v26.9.23 KNOWN reference path must not depend on ZCode.

---

## ggen-ecosystem

Owns cross-repository composition and qualification.

It shall validate ecosystem compatibility rather than invent independent semantic state.

---

## open-ontologies

May supply candidate extraction and ontology-scaffolding primitives for the UNKNOWN prose→semantics edge.

Admission remains separate.

---

# 5. Prose Compilation Architecture

## 5.1 Inputs

Accepted narrative may be:

* Vision 2030;
* WBPR;
* case study;
* operating policy;
* user-authored future-state prose.

## 5.2 Extraction

Candidate extractor produces:

```text
Actor
Object
Role
State
Transition
Capability
Trigger
Dependency
Invariant
Exclusion
Evidence
Authority
Postcondition
Falsifier
Metric
Successor
```

## 5.3 Candidate status

All extracted content initially has:

```text
standing = UNKNOWN
provenance = exact source span
```

## 5.4 Admission

SHACL plus domain admission rules verify that every required semantic object has:

* valid type;
* identity;
* required relationships;
* coherent boundaries;
* permitted vocabulary;
* no prohibited contradiction.

Only admitted candidate semantics become \(O^*\).

## 5.5 Deterministic projection

After admission:

```text
admitted RDF
→ deterministic semantic delta
→ deterministic WorkOrder graph
```

No second LLM interpretation is allowed for the same accepted graph revision.

---

# 6. sJira Ontology

The v26.9.23 ontology shall contain at least:

```text
sj:GoalCheckpoint
sj:WorkOrder
sj:Checkpoint
sj:MachineExperience
sj:CapabilityRequirement
sj:EvidenceRequirement
sj:Exclusion
sj:Falsifier
```

Required WorkOrder predicates:

```text
sj:subject
sj:postcondition
sj:dependsOn
sj:requiresCapability
sj:authorityCeiling
sj:consequenceClass
sj:evidenceHorizon
sj:acceptancePredicate
sj:falsifier
sj:exclusion
sj:successorPolicy
```

GoalCheckpoint predicates:

```text
sj:checkpointOf
sj:requiredProposition
sj:boundaryClass
sj:stopQuery
sj:successorCheckpoint
```

---

# 7. Standing Model

Standing shall be computed.

It shall not be trusted merely because a file contains:

```text
status = ALIVE
```

Derived standing depends on:

```text
exact subject identity
evidence identity
receipt validity
validator identity
applicable dependencies
current subject state
```

If a covered subject changes, standing may regress.

State classes:

```text
UNKNOWN
PARTIAL_ALIVE
ALIVE
BLOCKED
BUILD_BROKEN
UNSUPPORTED
REFUSED(reason)
SUCCESSOR
```

---

# 8. SA2A Contract

The required conserved tuple is:

```text
SemanticExecutionRequest {
  work_order
  subject
  postcondition
  capability
  evidence_horizon
  authority_ceiling
  consequence_class
  exclusions
  graph_digest
}
```

A digest shall be computed over the semantic contract.

The digest is checked at:

```text
sJira
→ SA2A
→ XaaS
→ provider
→ receipt
```

Mutation or loss of a required field refuses execution.

---

# 9. Provider Resolution

Provider selection is:

$$
Provider =
SELECT(
Capability,
Applicability,
Authority,
Cost,
Evidence,
Consequence
)
$$

The provider registry shall support at least:

```text
recipe-worker
Ash/Reactor
generator
formal planner
solver
external API
human
LLM
```

Provider selection shall prefer a deterministic admitted provider when one exists.

An LLM shall not outrank an equivalent deterministic provider for KNOWN work.

---

# 10. RecipeWorker

v26.9.23 introduces a deterministic reference provider.

A Recipe describes:

```text
recipe_id
applicability
argv / invocation
working_subject
precondition
expected_delta
verification_suite
consequence_class
```

RecipeWorker lifecycle:

```text
claim
→ validate subject
→ validate semantic digest
→ acquire lease
→ run BRCE-authorized invocation
→ observe result
→ invoke independent verifier
→ produce receipt
→ close/refuse
```

The worker has no semantic inference responsibility.

---

# 11. BRCE

The only DO path remains:

```text
parse
→ route
→ admit/refuse
→ diagnose/repair
→ construct
→ actuate
→ receipt
→ replay/hook
→ standing
```

No model, planner, proof or hook can independently create actuation authority.

---

# 12. Receipt Architecture

Every v26.9.23 critical-path receipt shall use one schema.

Required semantic dimensions:

```text
subject_identity
producer_identity
authority
precondition_evidence
consequence
postcondition_evidence
verification
replay
standing
timestamp/event identity
```

Old flat receipts may remain historical artifacts.

They do not count as v26.9.23 proof unless projected into the current schema by a validated adapter.

---

# 13. OCEL Architecture

Execution observations shall be expressible as OCEL 2 events.

Minimum event classes:

```text
WorkOrderCreated
CapabilityResolved
LeaseAcquired
ActuationStarted
ActuationCompleted
VerificationCompleted
ReceiptSealed
StandingChanged
FrontierChanged
MachineExperienceAdmitted
```

Relevant objects include:

```text
GoalCheckpoint
WorkOrder
Subject
Provider
Capability
Lease
Receipt
Repository
Commit
MachineExperience
```

OCEL records observation.

It does not manufacture authority.

---

# 14. Closed-Loop Architecture

The required last-mile loop is:

```text
WorkOrder
→ descriptor
→ capability resolution
→ materialization
→ lease
→ RecipeWorker
→ BRCE
→ verifier
→ receipt
→ OCEL
→ sJira.xaas_receipt
→ reconciliation
→ frontier
```

Acceptance requires proof that:

1. the completed order leaves the frontier;
2. eligible dependent work enters;
3. ineligible work remains fenced;
4. replay reaches the same semantic state.

---

# 15. MachineExperience

MachineExperience shall contain enough information to route a future equivalent case without semantic reinvention.

Required conceptual fields:

```text
problem_class
applicability_predicate
admitted_capability
provider_class
required_evidence
falsifiers
successful_verification
consequence_bounds
source_episode
```

Episode 1:

```text
UNKNOWN
→ exploration
→ verified result
→ MachineExperience
```

Episode 2:

```text
new subject
→ applicability match
→ KNOWN
→ deterministic route
```

The Episode-2 court shall fail if an LLM is required to rediscover the route.

---

# 16. Bootstrap Architecture

Cold bootstrap receives only durable system artifacts.

Allowed sources:

* git refs;
* canonical RDF;
* schema;
* receipts;
* OCEL/TransitionLog;
* provider registry;
* explicit configuration;
* authority rules.

Forbidden dependencies:

* Claude transcript;
* ZCode transcript;
* conversation memory;
* unstored plan;
* operator recollection.

Bootstrap output:

```text
current subjects
current identities
capabilities
active GoalCheckpoint
standing
frontier
BLOCKED/UNSUPPORTED/REFUSED state
```

Two independent bootstrap runs shall be semantically identical.

---

# 17. First-Mile Architecture

```text
Narrative
  ↓
candidate extraction
  ↓
provenance binding
  ↓
SHACL
  ↓
admission
  ↓
GoalCheckpoint
  ↓
current-state query
  ↓
semantic diff
  ↓
WorkOrder graph
```

The only permitted LLM edge is before semantic admission when meaning is genuinely novel.

Once the graph is admitted, replay of graph→WorkOrder manufacture is deterministic.

---

# 18. Last-Mile Architecture

```text
command exit 0
```

is insufficient.

The system requires:

```text
required world delta
+
independent observation
+
postcondition verdict
+
falsifier result
+
receipt
+
OCEL
+
derived standing
```

Only that combination can close a WorkOrder.

---

# 19. Stop Court

The stop-court runner shall accept:

```text
checkpoint = GC-26.9.23
```

and execute each child court declared in RDF.

Output:

```text
checkpoint
subject
court
standing
receipt
falsifier
```

The final SPARQL stop query returns true iff all required gates satisfy their semantic predicates.

No LLM participates in the stop calculation.

---

# 20. Failure Semantics

No generic “failed” state.

Failures are typed.

Examples:

```text
REFUSED(authority_missing)
REFUSED(admission_vacuous)
REFUSED(tuple_digest_mismatch)
REFUSED(exclusion_violated)
BLOCKED(dependency)
BLOCKED(external_answer)
UNSUPPORTED(provider_capability)
BUILD_BROKEN(toolchain)
UNKNOWN(novel_semantics)
```

A failed edge updates topology.

It does not automatically imply whole-graph failure.

---

# 21. Security and Authority

Secrets are represented as sensitive values in provider/plugin schemas.

Credentials are not semantic authority.

Authority must explicitly bind:

```text
actor/provider
subject
capability
consequence class
horizon
```

No SA2A request may escalate its own authority.

No generated artifact may inherit deployment/publish authority merely because its build passed.

---

# 22. Generated vs Handwritten

Preferred path:

```text
ontology
→ query
→ ggen/ggen_igniter
→ generated implementation
→ formal admission
→ runtime
```

Generated artifacts shall not be manually edited where a generator owns them.

Handwritten residue requires:

```text
HANDWRITTEN
reason
generator-capability gap
verification
```

Repeated handwritten patterns should become generator capability.

---

# 23. Planner Architecture

Planner selection shall depend on problem type.

Examples:

```text
hierarchical work → HDDL
state-space planning → PDDL/FOND
finite constraints → SAT/SMT/CP
business rules → declarative rules/Prolog
process conformance → OCEL/process mining
software derivation → template/generator
```

LLM planning is only a fallback for semantic UNKNOWN.

---

# 24. Migration from v26.9.22

## Phase M1 — Preserve

Preserve:

* v26.9.22 receipts;
* branches;
* predecessor work graphs;
* exact SHAs;
* historical OCEL;
* failed courts.

Do not rewrite history to conform to v26.9.23.

## Phase M2 — Extend ontology

Add:

* GoalCheckpoint;
* complete WorkOrder tuple;
* MachineExperience shapes;
* StopCourt vocabulary.

## Phase M3 — Canonicalize Friday work

Treat GC-FRI-0800 results as predecessor evidence.

v26.9.23 is its semantic successor, not a replacement of history.

## Phase M4 — Deterministic provider

Land RecipeWorker and at least one recipe.

## Phase M5 — SA2A conservation

Add tuple digest conservation across hops.

## Phase M6 — Receipt unification

Require new critical-path receipts to conform.

Historical receipts remain typed legacy evidence.

## Phase M7 — First-mile compiler

Land prose→candidate semantics→admission→delta.

## Phase M8 — Learning ratchet

Demonstrate UNKNOWN→MachineExperience→KNOWN.

## Phase M9 — Self-hosted successor

Use the resulting architecture to manufacture its next bounded GoalCheckpoint.

---

# 25. Verification Ladder

Run cheapest high-information checks first:

```text
ontology/SHACL
→ deterministic unit
→ tuple-conservation
→ provider integration
→ no-LLM episode
→ consequence court
→ frontier closure
→ cold replay
→ two-episode MachineExperience
→ multi-repo exact-head qualification
```

No unchanged failing command is rerun without a new hypothesis or repair.

---

# 26. Required Falsifiers

At minimum:

### F1

Delete a mandatory WorkOrder field.

Expected:

```text
REFUSED
```

### F2

Mutate SA2A tuple digest.

Expected:

```text
REFUSED(tuple_digest_mismatch)
```

### F3

Expose LLM credentials during the KNOWN no-LLM court.

Expected:

typed court failure/refusal.

### F4

Remove required consequence.

Expected:

WorkOrder remains non-ALIVE.

### F5

Delete receipt during cold replay.

Expected:

standing/frontier divergence.

### F6

Change covered subject after receipt.

Expected:

previous ALIVE standing no longer automatically applies.

### F7

Introduce an unclassified required repository.

Expected:

fleet checkpoint fails.

### F8

Attempt to turn newly discovered improvement into required current work without falsifying an active proposition.

Expected:

route to successor GoalCheckpoint.

---

# 27. Release Receipt

The final v26.9.23 release receipt shall include:

```text
exact checkpoint
exact graph digest
exact subject identities
repo SHAs
canonical ontology digest
schema digest
toolchain identity
provider registry identity
gate receipts
replay result
remaining frontier classifications
LLM invocation count on KNOWN reference path
standing
```

Expected:

```text
LLM_INVOCATIONS_ON_KNOWN_REFERENCE_PATH = 0
UNRECEIPTED_ACTUATION = 0
REQUIRED_UNKNOWN = 0
UNCLASSIFIED_REQUIRED_WORK = 0
STOP = true
```

---

# 28. Standing Definition

v26.9.23 is **ALIVE** only if its exact release checkpoint executes and its STOP receipt is reproducible.

Documentation completeness is not ALIVE.

Merged code is not ALIVE.

Green CI alone is not ALIVE.

A plan is not ALIVE.

A named receipt without validated contents is not ALIVE.

The crown is:

$$
\boxed{
Accepted\ Future
\rightarrow
Semantics
\rightarrow
Work
\rightarrow
Capability
\rightarrow
Authorized\ Consequence
\rightarrow
Evidence
\rightarrow
Replay
\rightarrow
STOP
}
$$

with zero LLM dependence on the demonstrated KNOWN path.

The two documents intentionally make **GC23-12 semantic self-hosting** the last v26.9.23 gate: once a new bounded future can enter through prose and manufacture its own finite semantic work graph, the architecture no longer needs another bespoke planning cycle for the same class of problem.
