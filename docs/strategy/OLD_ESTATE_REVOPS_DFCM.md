# Old-Estate RevOps DfCM Closure

**Manifest:** `old-estate-revops-dfcm-v1`  
**Age boundary:** repositories classified in the admitted owner-inventory sweep as created before `2026-05-19`  
**Planner:** `apps/ecosystem-cli/src/bin/old-estate-revops.rs`  
**Standing of this document:** specification for an executable planner; it does not establish live external connector standing.

## 1. Problem

The older repository estate contains several distinct things that look similar if they are flattened into a repository-name list:

- repository-specific RevOps implementations;
- reusable libraries that compose into RevOps but should remain generic;
- simulations and synthetic evidence that are useful only as falsifiers;
- framework/template repositories whose names can be mistaken for capabilities;
- workflows that construct an external intent but do not themselves have authority to produce the external consequence.

A quota-oriented sweep would destroy those distinctions. DfCM instead preserves the maximal reversible graph of lawful possibilities before selecting an irreversible edge.

The planner therefore answers a narrower question:

> Given the admitted old-estate observations, what role may each repository play in the revenue system, what evidence would verify that role, what observation would falsify it, and where must construction stop before external DO?

It does **not** answer:

> How can every old repository be made to produce activity?

`REFUSED` and `DEPENDENCY_ONLY` are successful outcomes when they preserve a real boundary.

## 2. Constitutional ordering

The scheduler follows this ordering:

```text
PRESERVE
  ↓
FENCE
  ↓
CLASSIFY
  ↓
EXPAND REVERSIBLE OPTIONS
  ↓
SCORE
  ↓
SELECT
  ↓
CONSTRUCT / VERIFY_ONLY / REFERENCE_ONLY / REFUSED
  ↓
VERIFY
  ↓
RECEIPT
  ↓
DO INTENT (only where applicable)
  ↓
EXACT AUTHORITY
  ↓
BRCE_REQUIRED
```

There is no edge in this executable from `BRCE_REQUIRED` to an external consequence.

That omission is deliberate. The planner does not contain a LinkedIn sender, CRM writer, browser automation path, payment action, merge action, or generic external-object mutation primitive.

## 3. Strategy classes

### `DIRECT`

The repository already owns a domain-specific RevOps role. New construction may deepen that role if its local verifier and falsifier remain satisfied.

### `COMPOSABLE`

The repository supplies a Chatman-specific cross-cutting capability that can be composed into the revenue system, but it is not the semantic authority for the business domain.

### `NEGATIVE_EVIDENCE`

The repository is valuable because it falsifies unsafe promotion rules. It enters the plan as `VERIFY_ONLY`, never as positive commercial evidence.

### `DEPENDENCY_ONLY`

The repository is a reusable or upstream-shaped primitive. The ecosystem may consume it; the old-estate campaign must not inject Chatman-specific GTM doctrine into it merely to create activity.

### `REFUSED`

The observed repository does not have an admitted RevOps subject. A suggestive repository name or generic starter template is insufficient evidence.

Typed refusal used by this manifest:

```text
REFUSED:NO_ADMITTED_REVOPS_SUBJECT
```

## 4. Exact authority law

`ecosystem_core::Authority` is exact-match authority, not a hierarchy.

Therefore:

```text
COMMUNICATE != MODIFY_EXTERNAL_OBJECT
MODIFY_EXTERNAL_OBJECT != COMMUNICATE
DRAFT != COMMUNICATE
APPROVE != COMMUNICATE
MERGE != COMMUNICATE
```

The old-estate planner currently recognizes two external-effect classes:

| Effect | Required exact authority | Planner consequence |
|---|---|---|
| `COMMUNICATE` | `Authority::Communicate` | `BRCE_REQUIRED` |
| `MODIFY_EXTERNAL_OBJECT` | `Authority::ModifyExternalObject` | `BRCE_REQUIRED` |

Without the exact grant, the decision is:

```text
REFUSED:AUTHORITY
```

With the exact grant, the decision is **not** `EXECUTED`; it is only:

```text
BRCE_REQUIRED
```

This means an authority grant may admit the *next boundary* without allowing the planning executable to perform that boundary's consequence.

## 5. DfCM scoring

Only `DIRECT`, `COMPOSABLE`, and `NEGATIVE_EVIDENCE` strategies receive a construction/verification score.

`DEPENDENCY_ONLY` and `REFUSED` always score zero so that a ranking algorithm cannot accidentally turn a reference or refusal into quota work.

The deterministic score is:

```text
reversibility = 11 - min(irreversibility, 10)

score =
    independent_edges
  × ecosystem_leverage
  × verifier_availability
  × reversibility
  × 100
  / max(construction_cost, 1)
```

The score is not truth and does not confer standing. It is a scheduling heuristic among already-classified lawful possibilities.

## 6. Admitted repository strategy graph

| Repository | Class | Role | Mode | External effect |
|---|---|---|---|---|
| `ggen` | DIRECT | manufacturing compiler | CONSTRUCT | NONE |
| `open-ontologies` | DIRECT | admission/receipt court | CONSTRUCT | NONE |
| `unrdf` | DIRECT | semantic operational graph | CONSTRUCT | NONE |
| `ostar` | DIRECT | simulation/proof laboratory | SIMULATE_ONLY | NONE |
| `chatmangpt` | DIRECT | legacy RevOps execution lab | CONSTRUCT | NONE |
| `bcinr` | DIRECT | publication lifecycle | CONSTRUCT | COMMUNICATE |
| `yawl` | DIRECT | champion-discovery workflow | CONSTRUCT | COMMUNICATE |
| `clap-noun-verb` | COMPOSABLE | typed RevOps control surface | CONSTRUCT | NONE |
| `pyn8n` | COMPOSABLE | integration fabric | CONSTRUCT | MODIFY_EXTERNAL_OBJECT |
| `knhk` | COMPOSABLE | brokered execution/evidence | CONSTRUCT | NONE |
| `chatman-nano-stack` | NEGATIVE_EVIDENCE | adversarial false-claim corpus | OBSERVE_ONLY | NONE |
| `Arazzo-Specification` | DEPENDENCY_ONLY | portable API workflow contract | DEPENDENCY_ONLY | NONE |
| `pm4py` | DEPENDENCY_ONLY | process-mining oracle | DEPENDENCY_ONLY | NONE |
| `ash_state_machine` | DEPENDENCY_ONLY | state-machine primitive | DEPENDENCY_ONLY | NONE |
| `ash_paper_trail` | DEPENDENCY_ONLY | resource-audit primitive | DEPENDENCY_ONLY | NONE |
| `ash_cloak` | DEPENDENCY_ONLY | sensitive-field protection | DEPENDENCY_ONLY | NONE |
| `ash_events` | DEPENDENCY_ONLY | event/replay primitive | DEPENDENCY_ONLY | NONE |
| `ash_oban` | DEPENDENCY_ONLY | background-work primitive | DEPENDENCY_ONLY | NONE |
| `ash_double_entry` | DEPENDENCY_ONLY | accounting primitive | DEPENDENCY_ONLY | NONE |
| `twitter` | REFUSED | name-only false friend | REFUSED | NONE |
| `chiefofstaffgpt` | REFUSED | name-only false friend | REFUSED | NONE |
| `pro-landing` | REFUSED | generic template | REFUSED | NONE |
| `helpdesk` | REFUSED | generic template | REFUSED | NONE |

## 7. Repository-specific laws

### 7.1 `ggen`: manufacture projections, never outreach authority

`ggen` is the manufacturing compiler for this system.

Its lawful path is:

```text
admitted semantic authority
  → query
  → template/projection
  → campaign schema / CRM schema / workflow / tests / docs
  → deterministic artifact
  → receipt
  → replay
```

Its falsifier is graph/projection drift or receipt/replay mismatch.

A generated message or workflow is an artifact. It is not evidence that a message was sent or that a workflow touched an external service.

### 7.2 `open-ontologies`: downstream gates remain independent

A requirement, work order, mutation, and emitted artifact are distinct objects. Admission of one does not excuse failure of another.

For RevOps this prevents:

```text
campaign admitted
  ⇒ message sent
```

Instead:

```text
CampaignRequirement
  ↓ CTQ
AdmittedCampaign
  ↓
WorkOrder
  ↓ alignment
MessageCandidate
  ↓ policy
PublicationIntent
  ↓ exact external authority
BRCE
  ↓
ExternalReceipt
```

### 7.3 `unrdf`: business truth is a semantic graph, not a CRM row

The intended domain projection includes at least:

```text
Person
Organization
Role
Problem
Evidence
Campaign
Interaction
Lead
Account
Opportunity
POV
Contract
Customer
Expansion
```

A CRM is a projection or operational surface over this graph; it is not permitted to silently redefine semantic identity.

### 7.4 `ostar`: simulation is a proof world

OSTAR is hard-fenced as `SIMULATE_ONLY`.

These implications are forbidden:

```text
SIMULATED_LEAD       -> REAL_LEAD
SIMULATED_MESSAGE    -> MESSAGE_SENT
SIMULATED_DEAL       -> REAL_OPPORTUNITY
SIMULATED_CONTRACT   -> CONTRACT_EXECUTED
SIMULATED_REVENUE    -> REVENUE_OBSERVED
```

Its value is pre-consequence testing: discover whether the proposed revenue process is coherent before any connector receives DO authority.

### 7.5 `chatmangpt`: requalify the historical execution lab

Historical CRM agents, lead scoring, pipeline movement, stalled-deal detection, ICP qualification, outreach-sequence semantics, deal progression, and contract telemetry are candidate evidence.

They do not receive current standing from commit history alone.

The correct loop is:

```text
historical capability
  → exact current head
  → compile/run
  → exercise real current boundary
  → verifier
  → falsifier
  → current receipt
  → standing
```

### 7.6 `bcinr`: publication requires consequence evidence

BCINR owns the lifecycle:

```text
TOPIC_SELECTED
→ DRAFT_EXISTS
→ REVIEWED
→ PUBLICATION_INTENT
→ COMMUNICATE authority
→ BRCE_REQUIRED
→ external connector consequence
→ RECEIPT_OBSERVED
→ PUBLISHED
```

A Markdown state marker is not sufficient to prove `PUBLISHED`.

### 7.7 `yawl`: champion discovery is not LinkedIn access

YAWL may model and execute admitted local workflow logic for candidate/path discovery, ranking, engagement-strategy construction, and process evidence.

Conceptual bridges remain conceptual until an observed connector proves otherwise.

Specifically:

```text
LinkedInBridge.analyzeNetwork
OutreachBridge.generatePlan
```

must not be interpreted as live LinkedIn access merely because those symbols occur in a workflow definition.

The final outreach effect remains `COMMUNICATE`, which this planner can advance only to `BRCE_REQUIRED`.

### 7.8 `clap-noun-verb`: typed control plane, not business truth

Candidate command families include:

```text
revops campaign inspect
revops lead admit
revops account inspect
revops opportunity qualify
revops pov propose
revops pipeline summary
revops receipt verify
revops attribution replay
```

The command algebra exposes an owning capability. It must not invent domain state.

### 7.9 `pyn8n`: choreography has external-object authority

A workflow can coordinate already-admitted work, retries, and handoffs.

Because an n8n workflow can mutate remote systems, the old-estate strategy carries `MODIFY_EXTERNAL_OBJECT` as its effect class. An exact `COMMUNICATE` authority therefore does not admit it.

Even exact `MODIFY_EXTERNAL_OBJECT` authority yields only `BRCE_REQUIRED` from this planner.

### 7.10 `knhk`: current evidence outranks archived economics

KNHK contributes broker, timing, authority, receipt, replay, and negative-control machinery.

Historical pricing, market-size, sales, ROI, or completion narratives are not current runtime evidence. The active implementation/evidence boundary wins whenever they conflict.

### 7.11 `chatman-nano-stack`: preserve the bad simulation as a test oracle

The archived fictional employment/outreach material is useful precisely because it demonstrates how coherent generated stories can look like external truth.

Required negative laws include:

```text
SIMULATED_APPLICATION != APPLICATION_SUBMITTED
GENERATED_OUTREACH    != MESSAGE_SENT
GENERATED_OFFER       != OFFER_RECEIVED
SIMULATED_REVENUE     != REVENUE_OBSERVED
PROFILE_NAME          != VERIFIED_PERSON
```

The repository is therefore `VERIFY_ONLY`, not constructable positive evidence.

## 8. Dependency-only composition

Dependency-only repositories are consumed, not rewritten for this campaign.

A lawful RevOps application may compose:

```text
Arazzo-Specification → portable API workflow description
PM4Py               → discovery/conformance oracle
ash_state_machine    → opportunity lifecycle
ash_events           → interaction/event ledger
ash_paper_trail      → mutation audit history
ash_cloak            → sensitive-field protection
ash_oban             → scheduled admitted work
ash_double_entry     → booked monetary consequence ledger
```

The last line is especially important:

```text
engagement != revenue
pipeline probability != revenue
meeting != revenue
proposal != revenue
```

Only admitted monetary consequences belong in the accounting ledger.

## 9. Refusal corpus

The following repositories are currently refused as RevOps subjects:

```text
twitter
chiefofstaffgpt
pro-landing
helpdesk
```

This does not mean they are useless repositories. It means the old-estate RevOps planner has no evidence-bounded reason to mutate them for this objective.

That is a DfCM feature: refusal preserves optionality and prevents semantic corruption.

## 10. CLI

### Validate invariants

```bash
cargo run -p ecosystem-cli --bin old-estate-revops -- check
```

### Render the entire admitted manifest

```bash
cargo run -p ecosystem-cli --bin old-estate-revops -- list
```

### Rank the default no-external-authority plan

```bash
cargo run -p ecosystem-cli --bin old-estate-revops -- plan none
```

Expected external edges remain authority-refused.

### Admit communication intent without actuating it

```bash
cargo run -p ecosystem-cli --bin old-estate-revops -- plan communicate
```

BCINR/YAWL should move from:

```text
REFUSED:AUTHORITY
```

to:

```text
BRCE_REQUIRED
```

They must never report `EXECUTED` from this tool.

### Admit external-object mutation intent without actuating it

```bash
cargo run -p ecosystem-cli --bin old-estate-revops -- plan modify-external-object
```

`pyn8n` may advance to `BRCE_REQUIRED`; BCINR/YAWL must remain `REFUSED:AUTHORITY` because authority is exact, not hierarchical.

### Inspect one repository

```bash
cargo run -p ecosystem-cli --bin old-estate-revops -- repo ggen
cargo run -p ecosystem-cli --bin old-estate-revops -- repo seanchatmangpt/yawl communicate
```

### Manufacture an exact-subject BLAKE3 planning receipt

```bash
cargo run -p ecosystem-cli --bin old-estate-revops -- \
  receipt <40-hex-git-sha> none
```

The receipt is created with `ecosystem_core::Receipt`, sealed using the canonical BLAKE3 implementation, and immediately verified before output.

A branch name such as `main` is rejected. Receipt subject identity must be a 40-hex Git commit.

## 11. Receipt semantics

The receipt records:

- manifest identity;
- age cutoff;
- repository count;
- requested exact authority;
- SELECT classification;
- reversible CONSTRUCT ranking;
- explicit absence of external DO;
- authority refusal count;
- BRCE-required count;
- excluded consequence classes;
- deterministic replay command;
- exact Git subject;
- BLAKE3 digest.

The receipt uses:

```text
Standing::Observed -> Standing::Candidate
Authority::Draft
```

because the artifact being receipted is a candidate execution strategy, not an executed commercial consequence.

## 12. Executable falsifiers

The binary contains tests for at least the following laws:

1. the manifest contains exactly the admitted 23 repository roles;
2. manifest identities are unique;
3. every entry has mission, verifier, and falsifier closure;
4. dependency-only repositories never construct and score zero;
5. refused false friends never construct and carry a typed refusal;
6. OSTAR cannot actuate an external outcome;
7. chatman-nano-stack remains negative evidence / verify-only;
8. communication effects refuse without exact authority;
9. communication authority advances only to `BRCE_REQUIRED`;
10. communication authority does not imply external-object mutation authority;
11. external-object mutation authority does not arise from a different grant;
12. plan rendering is deterministic;
13. active strategies have positive DfCM scheduling scores;
14. exact-subject receipts reject branch names/non-SHA subjects;
15. exact-subject receipts are BLAKE3-sealed and replay-verifiable.

## 13. What this implementation deliberately does not do

This change does not:

- send LinkedIn messages;
- scrape LinkedIn;
- assert a LinkedIn partnership or connector;
- mutate a CRM;
- run n8n against a remote system;
- deploy YAWL;
- create customer records;
- mark generated prospects as real leads;
- infer revenue from engagement;
- rewrite generic/upstream repositories;
- manufacture commits in repositories without an admitted subject;
- promote historical commit messages to current `ALIVE` standing;
- merge its own pull request.

Those omissions are part of the implementation contract, not missing features.

## 14. Next lawful expansion

Once this planner is exact-head verified, the next expansion is not "touch all 23 repos." It is to take the highest-ranked `DIRECT`/`COMPOSABLE` edge with an available verifier and construct a bounded closure triplet in its owning repository:

```text
OBSERVE / ADMIT
→ CONSTRUCT
→ VERIFY / RECEIPT
```

External-effect repositories add another fence:

```text
... → INTENT
    → EXACT AUTHORITY
    → BRCE
    → CONSEQUENCE RECEIPT
```

That keeps estate throughput high without converting repository count into a substitute for semantic work.
