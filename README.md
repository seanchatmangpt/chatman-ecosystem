# Chatman Ecosystem

## Standing-Bearing Software Manufacture

> **Generation is cheap. Standing is scarce.**

The Chatman Ecosystem is a constitutional control plane for manufacturing software, infrastructure, process, and machine-executable decisions from admitted evidence under explicit authority.

It is not a monolithic application and it is not an AI code generator. It is the composition root that answers a harder question:

> **When may an observed or generated artifact be treated as having standing?**

The governing equations are:

```text
A = μ(O*)
R = receipt(A)
```

where:

- `O` is a raw, partial, stale, or otherwise unadmitted observation;
- `O*` is observation admitted for a declared boundary;
- `μ` is lawful manufacture;
- `A` is the resulting artifact or consequence;
- `R` is a receipt binding identity, authority, execution, consequence, verification, and replay.

The executable lifecycle is therefore:

```text
O
→ parse
→ route
→ admit / refuse
→ O*
→ diagnose / repair
→ SELECT
→ CONSTRUCT
→ verify
→ authorize
→ BRCE DO
→ consequence A
→ receipt R
→ replay
→ standing
```

This repository implements the control plane around that lifecycle.

---

## Why this exists

LLMs and other generators can produce candidate code faster than humans can manually inspect the resulting state space. That does not make the output correct, authorized, reproducible, or operationally admissible.

Chateco treats **candidate production** and **standing** as different problems.

A model may propose a change. A planner may select a path. A generator may render code. A proof assistant may establish a theorem. A credential may make an API callable. None of those facts alone grants authority to change a consequential subject, and none establishes ecosystem-wide `ALIVE`.

The system therefore moves the engineering center of gravity from:

```text
generate → hope → deploy
```

to:

```text
observe → admit → manufacture → verify → authorize → actuate → receipt → replay → standing
```

The result is a software factory designed to make **plausibility insufficient**.

---

## Constitutional laws

The code is organized around a small set of non-negotiable invariants.

### 1. Observation is not authority

A fact may be observed without being admitted. An admitted fact may inform construction without granting permission to actuate.

```text
O ≠ O* ≠ authority
```

### 2. Exact subject identity is mandatory

Standing belongs to a specific subject: a commit SHA, file digest, document revision, artifact digest, external resource identity, or other exact object.

A successful execution against one SHA cannot be borrowed by another SHA.

### 3. Capability is not authority

Tool access, credentials, installed SDKs, API reachability, model capability, or administrative privilege are not equivalent to permission.

```text
can_do(x) ≠ may_do(x)
```

### 4. SELECT, CONSTRUCT, and DO are different authority classes

- **SELECT** chooses among admitted reversible possibilities.
- **CONSTRUCT** manufactures candidates, projections, proofs, plans, or intents.
- **DO** changes a consequential subject.

The first two do not implicitly confer the third.

### 5. Zero unreceipted actuation

Consequential mutation must cross a brokered authority boundary and produce a replayable receipt.

```text
DO ⇒ receipt
```

If the system cannot bind the consequence to authority, identity, and evidence, the lawful behavior is refusal.

### 6. Broker-only DO

BRCE — **Brokered Receipted Consequence Execution** — is the consequential path. Adapters submit intents; the broker admits or refuses them.

The canonical DFCM broker checks that a grant binds the exact subject SHA and exact intent digest before DO is admitted.

### 7. Evidence before standing

`ALIVE` is calculated from required evidence. It is not assigned because code looks complete, because CI is green, because an adjacent component passed, or because no work item remains.

### 8. Refusal is behavior

Invalid, stale, unauthorized, conflicting, malformed, unsupported, or tampered states must remain distinguishable.

A typed refusal is a successful execution of a safety boundary, not a degraded success state.

### 9. Canonical source before projection

Canonical machine-readable sources outrank generated views. Generated documentation, code, manifests, and indexes are projections unless explicitly declared otherwise.

### 10. Repository is not project

Repository, project, capability, role, workflow, artifact, receipt, and release are separate identities. The composition root does not collapse them into one object merely because they are related.

---

## Executable Definition of Done

Edition 2 of the research program changes completion from narrative to executable evidence.

For a release-scoped claim, the DFCM Definition of Done requires all of the following:

1. every required component is `ALIVE`;
2. every required `ALIVE` component owns an execution receipt;
3. every `executed_sha` exactly equals the admitted component SHA;
4. every required dependency is `ALIVE`;
5. every declared required release role is provided by an `ALIVE` required component.

The executable predicate lives in:

```text
scripts/dfcm_autonomic_finish.py
```

Run it directly:

```bash
python3 scripts/dfcm_autonomic_finish.py --definition-of-done
```

Exit semantics:

```text
0  computed DONE
2  typed REFUSED
3  lawful but incomplete
```

Run the DFCM observation / selection cycle:

```bash
python3 scripts/dfcm_autonomic_finish.py --limit 1
```

The cycle is:

```text
OBSERVE → EVALUATE_DOD → SELECT
```

and terminates as one of:

```text
DONE
CONTINUE
REFUSED:NO_LAWFUL_FRONTIER
```

An empty frontier is **not** completion.

---

## DfCM: Design for Combinatorial Maximalism

DfCM preserves the largest bounded set of lawful, reversible possibilities before irreversible selection.

The point is not to enumerate every imaginable action. The point is to avoid collapsing the solution space before the system has evidence that a collapse is necessary.

In the executable controller, repair candidates are ranked using evidence already present in the dependency graph, including:

- transitive dependency relief;
- direct dependency relief;
- reversibility;
- evidence cost;
- authority cost.

The preferred frontier is therefore not merely “the easiest next task.” It is the highest-value reversible move under the admitted graph.

```text
failed edge ≠ failed graph
```

One blocked transport, verifier, provider, or authority edge changes topology. It does not automatically invalidate every other lawful path.

---

## Standing vocabulary

The repository uses explicit epistemic states rather than a generic pass/fail flag.

```text
UNKNOWN
OBSERVED
CANDIDATE
PARTIAL_ALIVE
ALIVE
BLOCKED
BUILD_BROKEN
UNSUPPORTED
REJECTED
SUPERSEDED
```

The most important distinctions are:

```text
UNKNOWN      ≠ ADMITTED
UNSUPPORTED  ≠ REFUSED
OBSERVED     ≠ EXECUTED
CI_GREEN     ≠ STANDING
CHECKPOINT   ≠ CROWN
```

Standing is scoped to an exact subject and evidence boundary.

---

## Repository role

This repository is the **composition root** for the Chatman Ecosystem. It owns constitutional identity and cross-project standing, not every project implementation.

| Surface | Responsibility |
|---|---|
| `crates/ecosystem-core/` | identities, subjects, standing, authority, receipts, catalog, projections, Crown evaluation |
| `crates/ecosystem-runtime/` | replaceable runtime, storage, governor, connector, and protocol adapters |
| `apps/ecosystem-cli/` | fail-closed operator and CI interface |
| `catalog/` | canonical TOML capability, relationship, and release metadata |
| `release/` | dependency-closed release graphs and admitted component subjects |
| `receipts/` | source receipts and replay evidence |
| `views/generated/` | deterministic projections; do not hand-edit |
| `platform-console/` | deployable enterprise/platform control surface and live evidence corpus |
| `scripts/` | Crown, DFCM, release, evidence, replay, and repair courts |
| `tests/` | positive, adversarial, refusal, replay, and DoD fixtures |
| `docs/` | research program, constitutional theory, operating doctrine, release records, and design decisions |

The repository coordinates independently releasable systems including ggen, ggen-marketplace, ggen-legacy, mfact/procint, Praxis, GymAct, AutoFDE, CASTLE, MU, and related execution/proof surfaces.

Those systems retain their own identities and evidence boundaries.

---

## Ecosystem manufacturing model

The research program treats the ecosystem as a set of bounded manufacturing roles rather than one giant runtime.

```text
public ontology / admitted semantics
                ↓
              ggen
         lawful projection
                ↓
        candidate artifacts
                ↓
      Lean / mfact / SHACL
        admission / proof
                ↓
          Rust / WASM
       bounded execution
                ↓
              BRCE
      authorized consequence
                ↓
       receipt + OCEL log
                ↓
             replay
                ↓
            standing
```

A useful shorthand is:

> **ggen renders. Lean admits. mfact certifies. BRCE actuates. Receipts remember. Replay tests continuing standing.**

No one layer is allowed to self-certify the entire chain.

---

## Public ontology before private convention

Chateco treats shared semantics as infrastructure.

The intended semantic stack includes public standards and ontologies such as RDF/RDFS, OWL 2, SKOS, SHACL, PROV-O, DCAT, DCTERMS, ORG, FOAF, ODRL, QUDT, SOSA/SSN, and OCEL where they apply.

The rule is simple:

> Do not invent a private domain class or property when a suitable public semantic authority already exists.

Public semantics are mapped into bounded canonical graphs. Runtime stores, source files, indexes, syntax trees, and generated views are projections of different concerns; no single storage engine becomes semantic sovereignty by implementation accident.

---

## BRCE authority boundary

The DFCM broker refuses ambient DO authority.

A consequential grant must bind at least:

```text
subject_sha
intent_digest
scope
expires_at
authority_id
```

The canonical repair scope currently admitted by `admit_do()` is:

```text
BRCE:VERIFY_REPAIR_ONLY
```

Subject drift, intent drift, malformed grants, unsupported scope, or missing authority are typed refusals.

Credentials may make an operation technically possible. They do not make it lawful.

---

## Receipts and replay

A receipt is not a log line saying that something happened.

A useful receipt binds enough information to answer:

- **what exact subject changed?**
- **under whose authority?**
- **from which admitted observation?**
- **through which manufacturing path?**
- **what consequence was observed?**
- **which verifier established the local claim?**
- **can the evidence be replayed without re-actuating?**

The DFCM controller emits hash-chained receipts and validates chain continuity and digest integrity during replay.

Replay is deliberately separated from re-execution. A replay court verifies evidence; it must not silently actuate again.

---

## Build and verify

The repository Crown is the highest local verification court.

```bash
./scripts/crown.sh
```

The Crown currently executes, among other gates:

```text
release graph
standing evidence
mandatory Crown edges
v2030 executable Definition of Done
Python tests
cargo fmt
cargo clippy
cargo test
rustdoc
cargo-deny
cargo-machete
catalog validation
receipt verification
projection check
architecture check
storage differential verification
Gall capsule
cold-cache replay
exact GitHub subject read
artifact transfer
Crown verification
```

The individual composition-root checks are useful when diagnosing a narrower failure:

```bash
cargo run --locked -p ecosystem-cli --bin ecosystem -- catalog validate
cargo run --locked -p ecosystem-cli --bin ecosystem -- receipt verify-all
cargo run --locked -p ecosystem-cli --bin ecosystem -- projection check
cargo run --locked -p ecosystem-cli --bin ecosystem -- architecture check
cargo run --locked -p ecosystem-cli --bin ecosystem -- storage verify
cargo run --locked -p ecosystem-cli --bin ecosystem -- crown --verify
```

Release graph verification:

```bash
python3 scripts/verify_release.py --check-refs
python3 scripts/verify_standing_evidence.py
python3 scripts/verify_crown_edges.py
python3 scripts/v2030_definition_of_done.py --self-test
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

A strict release admission is expected to fail until every required exact subject has independently earned the required standing.

---

## How to add a capability

Do not start by adding an endpoint.

Start by identifying the semantic and authority contract.

### 1. Define the subject

Name the exact capability, owner, repository, version/ref, and evidence boundary.

### 2. Reuse public semantics

Map the capability to existing public ontology where possible. Add private semantics only for a real uncovered concept.

### 3. Admit the observation

Define what must be known before construction is lawful and what must be refused when that evidence is absent or contradictory.

### 4. Preserve SELECT / CONSTRUCT / DO separation

A planner or model may construct an intent. It may not self-grant consequential authority.

### 5. Add negative fixtures

Test malformed, stale, duplicate, conflicting, unauthorized, unsupported, tampered, and exact-subject-drift cases.

### 6. Bind execution evidence

If the capability is claimed `ALIVE`, name the owning execution receipt and exact executed subject.

### 7. Add replay

The evidence must survive independent replay without hidden re-actuation.

### 8. Update the release graph

Only after the component has its own standing should the composition root use it in a larger Crown claim.

---

## Generated artifacts

Generated output is disposable unless a governing contract explicitly says otherwise.

Before editing any generated surface, identify its source and generator. Prefer:

```text
canonical source → generator → projection → verification
```

over:

```text
hand edit projection → semantic drift
```

The composition root is intentionally hostile to manual synchronization that can instead be derived from one admitted semantic source.

---

## CI is evidence, not truth

GitHub Actions is an execution environment, not the source of correctness.

A queued workflow is not an executed verifier. A green job on the wrong SHA is not evidence for the current subject. A successful child component does not grant standing to its parent composition.

The minimum question is always:

```text
Which verifier executed against which exact subject, and where is its receipt?
```

Local source capsules and exact-head hosted execution are complementary evidence rails.

---

## Security model

Chateco treats security primarily as controlled reachability.

A secure system is not merely one with strong authentication. It is one in which forbidden consequences are unreachable through every admitted path.

That means security controls appear throughout the manufacturing chain:

```text
observation boundary
→ admission policy
→ capability boundary
→ authority boundary
→ construction sandbox
→ supply-chain evidence
→ BRCE broker
→ consequence observation
→ receipt integrity
→ replay
```

Machine-speed defense requires machine-speed verification and repair, but machine speed does not justify ambient authority.

---

## What this repository does not claim

This repository does **not** treat any of the following as automatically established:

- universal correctness of generated software;
- ecosystem-wide `ALIVE` from one successful component;
- Fortune-5 production acceptance without the corresponding customer/provider evidence;
- compliance certification without the required independent authority;
- exact cloud equivalence without differential validation against the relevant provider behavior;
- autonomous production DO without explicit broker authority;
- scientific truth merely because the research manuscript builds successfully.

Publication standing, software standing, operational standing, enterprise standing, and scientific standing are separate claims.

---

## Research program

The code is the experimental apparatus for **The Chateco Research Program: Standing-Bearing Manufacture and Executable Completion**.

The research program develops the codebase around several connected ideas:

- the Chatman Equation: `A = μ(O*)`;
- receipt calculus: `R = receipt(A)`;
- admission theory and typed refusal;
- public ontology as constitutional infrastructure;
- Recursive Workflow and partial-order manufacture;
- DfCM and bounded combinatorial completeness;
- proof-carrying projection across RDF, ggen, Lean, Rust, and receipts;
- BRCE and zero unreceipted actuation;
- OCEL evidence and replay;
- executable cloud world models;
- enterprise and marketplace standing;
- Toyota-style software manufacturing and factory economics;
- post-AGI software manufacture where intelligence is abundant but standing remains scarce.

The repository is not merely a case study for the theory. It is the instrument used to attempt to falsify it.

---

## Recommended entry points

| Goal | Start here |
|---|---|
| Understand the laws | [`CONSTITUTION.md`](CONSTITUTION.md) |
| Understand the architecture | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Operate the system | [`docs/OPERATIONS.md`](docs/OPERATIONS.md) |
| Inspect canonical capability metadata | [`catalog/`](catalog/) |
| Inspect the release graph | [`release/`](release/) |
| Inspect the DFCM controller | [`scripts/dfcm_autonomic_finish.py`](scripts/dfcm_autonomic_finish.py) |
| Inspect executable completion | [`scripts/v2030_definition_of_done.py`](scripts/v2030_definition_of_done.py) |
| Run the Crown | [`scripts/crown.sh`](scripts/crown.sh) |
| Inspect receipts | [`receipts/`](receipts/) |
| Inspect generated projections | [`views/generated/`](views/generated/) |
| Inspect platform behavior | [`platform-console/`](platform-console/) |
| Read the research/book corpus | [`docs/`](docs/) |

---

## The operating question

When a system, agent, developer, or workflow says that something is done, do not ask only whether the artifact exists.

Ask:

> **What exact observation was admitted?**  
> **What law manufactured the artifact?**  
> **Who authorized the consequence?**  
> **Which exact subject executed?**  
> **Where is the receipt?**  
> **Does replay preserve the claim?**

That is the difference between generated software and software with standing.
