# RFC QME-1 — Qualified Machine Experience

Status: Draft Standard
Version: 26.9.29
Canonical subject: seanchatmangpt/chatman-ecosystem
Authority: NONE. This specification defines qualification; it grants no consequential authority.

## Thesis
A mature system SHOULD accumulate qualified machine experience: reusable positive and negative knowledge bound to exact subjects, evidence horizons, authority ceilings, falsifiers, receipts and replay. New capabilities inherit admitted semantics and hardening instead of restarting qualification from zero.

## Normative laws
1. **Exact subject.** Evidence, standing, receipts and qualification MUST bind an exact subject identity. Standing MUST NOT transfer by analogy.
2. **No Hidden Semantics.** Consequential meaning MUST have one inspectable canonical owner. Projection MUST preserve provenance and MUST NOT invent private semantics.
3. **Consequence separation.** Candidate != Truth != Authority != DO != Standing. SELECT and CONSTRUCT MUST NOT imply consequential DO.
4. **Independent observation.** A consequential postcondition MUST be observed independently of the actor claiming completion.
5. **Replay safety.** Replay MUST be non-actuating unless separately admitted as a new consequence.
6. **Canonical ownership.** A semantic concept MUST have one canonical owner; consumers SHOULD link/project/derive rather than copy.
7. **Negative knowledge.** A rejected capability, failed path, removed workaround or historical constraint MAY be inherited only with its subject, boundary, conditions and falsifier.
8. **Reverse Chesterton.** Removal of a guard requires evidence that its originating function is obsolete for the same subject and boundary.
9. **Adversarial Constraint Distillation.** Repeated failures SHOULD be distilled into typed constraints, schemas, generators, policies or falsifiers.
10. **Metallurgical hardening.** Qualification is cumulative: each admitted failure mode SHOULD increase inherited hardening without silently widening authority.
11. **Semantic manufacture.** Generated projections MUST name canonical source, generator/profile identity and digest; generated consumer surfaces SHOULD NOT be hand edited.
12. **External absorption.** External capabilities enter as candidates/evidence. Their native authorization or success semantics MUST NOT automatically acquire local authority.

## Null and negative-value calculus
Let Q(c,s,h) be the qualification value of capability c for exact subject s at evidence horizon h.
Q=0 (MX0) when the capability adds no admitted net value.
Q<0 when capability gain is dominated by added hidden semantics, authority, consequence, unverifiable state, irreversibility, or regression surface.
MXinf denotes an unbounded or not-yet-bounded consequence term and therefore MUST fail closed.
A locally useful capability MAY therefore be non-conformant or negative.

## Expanded Chicago qualification
Qualification is conjunctive, not compensatory:
Q+ = ExactSubject ∩ Provenance ∩ CanonicalSemantics ∩ AuthorityBound ∩ ConsequenceBound ∩ IndependentObservation ∩ Receipt ∩ ReplaySafe ∩ Falsifiers ∩ Migration.
A missing conjunct MUST NOT be offset by strength elsewhere.

## Negative-knowledge record
A reusable exclusion MUST carry:
- id and exact subject
- boundary and originating condition
- observation/evidence horizon
- excluded behavior
- authority/consequence impact
- falsifier for continued applicability
- successor/re-entry rule
- receipt/replay identity

## Profiles
Profiles are additive constraints and MUST NOT weaken the core.
The FIBO Finance profile binds financial concepts to canonical FIBO identifiers where applicable, requires exact instrument/account/party/effect identity, and treats policy, allocation, valuation and semantic inference as evidence until independently authorized.

## Reference implementation mapping
These mappings are evidence, not normative dependencies:
- GraphLaw: semantic law-state and reasoning.
- Ash / ash_graphlaw: application projection.
- ash_r2rml: virtual knowledge graph observation/federation.
- ash_a2a / SA2A: powerless PreparedEffect, receipt and replay consequence protocol.
- Affidavit: cryptographic evidence/trust.
- Beam4PM: process evidence and accumulated machine experience.
- XaaS: runtime composition.
- ggen-marketplace: canonical writable semantic manufacture.
- CASTLE: product-level consequential constitution.

## Conformance
A conforming implementation MUST expose machine-readable:
subject, profile/version, evidence horizon, canonical owners, authority ceiling, consequence class, negative-knowledge records, falsifiers, receipt identity and replay policy.

The executable conformance entrypoint MUST reject at least:
- subject mismatch;
- hidden/private consequential semantics;
- authority inferred from evidence/signature/plan/receipt;
- replay that repeats a consequence;
- self-observed completion for consequential DO;
- MXinf/unbounded consequence;
- generated projection without provenance;
- external allow/decision promoted directly to local DO;
- removed guard without same-subject Reverse-Chesterton evidence.

## Migration
1. Inventory duplicate terms and private semantics.
2. Bind each concept to one canonical owner.
3. Preserve old names only as explicit compatibility aliases.
4. Project/link rather than copy prose or implementation.
5. Convert recurring failures into negative-knowledge records and falsifiers.
6. Require exact-subject receipts before retiring old paths.
7. Delete superseded duplicate implementations only after parity is observed.

## Non-normative rationale
The objective is declining required intelligence over time: mature systems remember what failed, why boundaries exist, how authority is separated, and how outcomes are independently proven. Experience compounds only when it is portable without becoming implicit authority.


## QME-1 hardening amendment — 26.9.29

The conformance record now makes the accumulated-hardening model executable rather than implicit.

### Anti-vacuity
A negative result is qualifying evidence only when the attempted violation reached the declared boundary. `attempt.observed=false` MUST be refused as `VACUOUS_COURT`. Observing the forbidden result MUST be refused as `VIOLATION_OBSERVED`.

### Authority non-promotion
When the authority ceiling includes DO, the authority basis MUST NOT be capability, evidence, signature, plan, receipt, semantic truth, ontology inference, model output or an external allow decision. These may constrain or support a grant; they do not manufacture it.

### Reverse Chesterton
A guard or historical constraint MAY be retired only with same-subject evidence of its originating function and an explicit falsifier that would invalidate the retirement. Cleaner-looking replacement code is not sufficient evidence.

### External absorption
External frameworks, protocols and research enter as capability candidates. Their useful semantics MAY be admitted and projected through local owners, but an external authorization or success result MUST NOT promote directly to local DO.

### Null baseline and negative value
A capability is compared with the null system, not merely with task failure. A record with negative net qualified value MUST NOT claim ALIVE. Unbounded value or consequence terms are MXinf and fail closed.

### Metallurgical hardening
Hardening means structural inheritance of negative knowledge. A counterexample SHOULD become the smallest general invariant that blocks its failure class, with a reusable killer fixture. Accumulating special-case checks without generalization is not considered mature hardening.

### Machine-readable law surface
`conformance/qme-1/laws.json` is the machine-readable law/refusal table. The unit court requires killer coverage for every semantic refusal emitted by the QME court.
