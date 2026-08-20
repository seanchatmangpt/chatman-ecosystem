# Dyson SHACL

> **Subject identity:** `dyson:dyson-shacl:6dea66be416c`
> **Domain:** `ontology`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Dyson SHACL** exists because it changes a concrete decision inside **Part III — The Dyson Ontology**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Dyson SHACL**, the primary state variables include **IRI**, **triple**, and **class**; the control or consequence variables include **property**, **shape**, and **provenance**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Dyson SHACL** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [Shape Constraints](12-01-shape-constraints.md)
- [Orbital Safety Shapes](12-02-orbital-safety-shapes.md)
- [Energy Shapes](12-03-energy-shapes.md)
- [Material Provenance Shapes](12-04-material-provenance-shapes.md)
- [Authority Shapes](12-05-authority-shapes.md)
- [Receipt Shapes](12-06-receipt-shapes.md)
- [Fail-Closed Admission](12-07-fail-closed-admission.md) For **Dyson SHACL**, this reusable domain rule is evaluated against `dyson:dyson-shacl:6dea66be416c`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

For **Dyson SHACL**, semantic identity is executable infrastructure. A minimal pattern binds a physical subject to stable identity and provenance:

```turtle
<dyson:dyson-shacl:6dea66be416c> a ex:DysonSubject ;
    dcterms:identifier "dyson:dyson-shacl:6dea66be416c" ;
    prov:wasDerivedFrom <urn:observation:df84d180b1> .
```

The prefix spelling is not the point. The point is joinable meaning: identity, quantity/unit, agent or instrument, provenance, policy, and constraint must survive projection into APIs, simulation, generation, and receipts. SHACL should reject missing required edges before malformed graph state reaches construction. For **Dyson SHACL**, this reusable domain rule is evaluated against `dyson:dyson-shacl:6dea66be416c`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:dyson-shacl:6dea66be416c` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | IRI, triple, class with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | property, shape or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Dyson SHACL**, Create one positive RDF fixture and negative SHACL fixtures for missing identity and missing unit. If malformed graphs still generate artifacts, semantic admission is ornamental rather than executable.

## Questions the design must answer

1. For **Dyson SHACL**: Which public term already carries the intended semantics?
2. For **Dyson SHACL**: What identity makes observations joinable without guesswork?
3. For **Dyson SHACL**: Which SHACL shape must fail before malformed state reaches generation?

## Executable representation

```json
{
  "subject": "dyson:dyson-shacl:6dea66be416c",
  "topic": "Dyson SHACL",
  "state": "OBSERVED_OR_PROPOSED",
  "provenance": "required",
  "unit_or_schema": "required",
  "uncertainty_or_quality": "required",
  "validity": "bounded",
  "consumer": "named downstream admission rule"
}
```

## Failure modes and counterexamples

- Two similar identifiers are merged without explicit equivalence, contaminating provenance and generation.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Dyson SHACL**.
- **Hidden assumption:** IRI or triple is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Dyson SHACL**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:dyson-shacl:6dea66be416c`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Dyson SHACL** subject/revision is named.
- [ ] Required IRI, triple, and class observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Dyson SHACL** is admitted, downstream systems may consume its IRI, triple, and class claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Dyson SHACL** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
