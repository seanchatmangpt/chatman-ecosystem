# XPROD-001 — Chatman Ecosystem Cross-Product Court

**Status:** IMPLEMENTED CANDIDATE  
**Release:** v26.9.24  
**Owner:** `seanchatmangpt/chatman-ecosystem`  
**Authority ceiling:** `NONE`  
**Claim ceiling:** `COMPOSITIONAL_CORRESPONDENCE_ONLY`

## Purpose

`chatman-ecosystem` owns ecosystem-wide cross-product evaluation. Individual repositories remain responsible for producing bounded evidence in their own domains; this court evaluates whether those independently produced dimensions are bound to one declared semantic subject through explicit per-repository exact heads and support the declared cross-dimensional relations without contradiction.

It is a **court of courts**, not another planner, solver, runtime, certificate authority, or actuation broker.

The canonical evaluation space is:

\[
\mathcal X = R \times F \times B \times E \times V
\]

where:

- `R` — repository / exact subject identities;
- `F` — formalism or evidence dimensions such as HDDL, FOND, TLA+, POWL, OCEL 2.0, BRCE, and receipts;
- `B` — semantic boundary under evaluation;
- `E` — observed result / standing;
- `V` — validator and tool identities.

The implementation does **not** enumerate the entire Cartesian product. A case explicitly declares the dimensions and cross-dimensional relations it requires.

## Ownership boundary

| Concern | Owner |
|---|---|
| UNKNOWN formal-method exploration and TLA model checking experiments | `autofde-lab` |
| reusable semantic/formalism patterns | `ggen-marketplace` |
| deterministic manufacture | `ggen` |
| ontology/project projection | `ggen_igniter` |
| agent/protocol/planning runtime evidence | `ash_a2a` |
| world/fault experiments and OCEL execution evidence | `gymact` |
| control-plane/work-order subjects | `xaas` |
| process discovery/conformance | `beam4pm` / `wasm4pm` |
| evidence certification profiles | `affidavit` |
| ggen-family release composition | `ggen-ecosystem` |
| **cross-repository, cross-formalism composition evaluation** | **`chatman-ecosystem`** |

No producer receives authority from appearing in a cross-product case.

## XPROD evidence record

Every evidence record binds:

- stable evidence identity;
- shared semantic subject ID at the case level;
- producer repository plus its exact 40-hex subject SHA;
- formalism/evidence dimension;
- claim identity;
- artifact digest;
- validator identity;
- validator executable/configuration digest;
- observed result;
- optional counterexample digest;
- `authority = NONE`.

An invalid or authority-bearing projection is refused before evaluation.

## Cross-dimensional relations

XPROD evaluates declared relations, for example:

\[
HDDL(S) \leftrightarrow TLA(S)
\]

for a shared authority-conservation claim,

\[
FOND(S) \leftrightarrow TLA(S)
\]

for a nondeterministic safety claim,

\[
OCEL(S) \leftrightarrow POWL(S)
\]

for execution conformance, and

\[
BRCE(S) \leftrightarrow Receipt(S)
\]

for receipted consequential execution.

A relation is admitted only when both dimensions provide `PASS` evidence for the same declared claim and each evidence item matches its repository's exact subject binding in the case. Cross-repository correspondence never assumes that different repositories share one Git SHA.

## Mutant requirement

Positive agreement alone is insufficient. A case may require negative controls such as:

```text
mutant: double-writer-without-serialization
formalism: TLA+
expected: COUNTEREXAMPLE
```

If a required mutant unexpectedly returns `PASS`, the court emits:

```text
REFUSED:MUTANT_SURVIVED:<mutant-id>
```

This prevents vacuous or non-discriminating verification from creating cross-product standing.

## Standing calculus

The evaluator emits one deterministic receipt with its own SHA-256 digest.

- `ALIVE` — every required dimension is present, every declared relation is satisfied, and every required mutant fails closed as expected.
- `BLOCKED` — required evidence is missing.
- `REFUSED` — contradictory identity, failed relation, ambiguous mutant evidence, or survived mutant.
- `PARTIAL_ALIVE` — reserved for structurally valid but incomplete evaluation states not otherwise blocked/refused.

`ALIVE` means only that **the declared composition evidence is internally correspondent under this court**. It does not upgrade the underlying producer claims, prove unmodeled behavior, grant deployment/release standing, or authorize `DO`.

## Constitutional invariant

\[
CrossProductAgreement \not\Rightarrow Authority
\]

The implementation enforces this as data: `EvidenceRecord.authority` must be exactly `NONE`, and every output receipt has `authority = NONE`.

## Required evidence dimensions

The court distinguishes evidence production from evidence composition. A producer record is admissible only when it names the exact subject and validator that generated its claim; the cross-product court then evaluates relations between those already-bounded claims.

| Dimension | Required identity | What a PASS can establish | What it cannot establish |
|---|---|---|---|
| HDDL | domain/problem + producer SHA | declared hierarchical-plan property for the admitted model | runtime execution or authority |
| FOND | domain/problem + producer SHA | declared nondeterministic policy property | production environment fidelity |
| TLA+ | spec/config + verifier identity | bounded formal property under the checked model | unmodeled production correctness |
| POWL | model + producer SHA | declared process-structure property | observed conformance by itself |
| OCEL 2.0 | log digest + producer SHA | observed object-centric event evidence | causal truth beyond the log |
| BRCE | protocol/profile + producer SHA | consequence-control contract evidence | an authority grant |
| Receipt | receipt digest + verifier identity | integrity and exact-subject evidence | the truth of claims not covered by its verifier |

A relation therefore composes **standing**, never ambient privilege. Missing dimensions remain missing; a neighboring repository, similar claim, or successful validator for a different subject cannot fill the hole.

## Primary falsifiers

XPROD-001 is falsified by any executable witness where a required relation reaches `ALIVE` despite one of these conditions:

- either side of the relation is absent, non-PASS, or bound to the wrong exact subject;
- a required negative-control mutant survives;
- one evidence record carries authority other than `NONE`;
- two repositories are forced to share one Git SHA rather than their declared repository-specific subjects;
- a deterministic replay of the same case yields a different receipt digest;
- a producer claim is silently upgraded beyond its own evidence ceiling.

These are topology-level composition failures. They do not reinterpret a producer's local verifier result.

## Executable surface

```bash
PYTHONPATH=. python3 -m scripts.release_train.cross_product_court path/to/case.json
```

Exit status is `0` only for `ALIVE`; all other standing returns `2` while still printing the deterministic receipt.

## XPROD-001 bounded crown

The current PR qualifies the **court machinery**, not a live ecosystem-wide subject. Its executable synthetic court proves:

1. seven dimensions can be composed: HDDL, FOND, TLA+, POWL, OCEL 2.0, BRCE, receipt;
2. shared-subject cross-dimensional relations are evaluated explicitly;
3. one semantic subject can bind multiple repository-specific exact heads;
4. missing evidence remains `BLOCKED` rather than guessed;
5. per-repository subject identity split and unbound repositories are `REFUSED`;
6. projections cannot carry authority;
7. a survived negative-control mutant is `REFUSED`;
8. receipt output is deterministic.

A later evidence PR should bind XPROD-001 to real exact-head outputs from the producing repositories. This PR does not claim those external results were executed here.

## No-actuation guarantee

The exact-head workflow rejects ambient consequential surfaces in the implementation/tests. The court consumes files and emits evaluation data only. It does not perform network writes, subprocess execution, cloud actions, Git mutation, merge, publish, deploy, or BRCE `DO`.
