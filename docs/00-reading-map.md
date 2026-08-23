# How to Read This Documentation

The repository contains distinct documentation strata that must not collapse into one timeline:

1. **current capability documentation** grounded in executable source and exact evidence;
2. the **preserved v26.8.18 operational snapshot**, authoritative only for its stated release subject;
3. long-form constitutional/research doctrine;
4. the future/frozen v26.9.1 proof corpus.

Start with [`DOCUMENTATION-INVENTORY.md`](DOCUMENTATION-INVENTORY.md) to determine which file owns a fact and whether it is current, historical, generated, future, or local.

## Diátaxis first

For a current capability, choose by what you need to do:

| Reader need | Role | Replicated-evidence example |
|---|---|---|
| learn by completing a bounded success path | Tutorial | [`diataxis/tutorials/replicated-evidence-state.md`](diataxis/tutorials/replicated-evidence-state.md) |
| accomplish or diagnose a concrete task | How-to | [`diataxis/how-to/qualify-replicated-evidence.md`](diataxis/how-to/qualify-replicated-evidence.md) |
| look up exact contracts, states, schemas, refusals | Reference | [`diataxis/reference/replicated-evidence-state.md`](diataxis/reference/replicated-evidence-state.md) |
| understand design rationale and boundaries | Explanation | [`diataxis/explanation/replicated-evidence-currentness.md`](diataxis/explanation/replicated-evidence-currentness.md) |

A canonical fact has one authoritative home. For replicated evidence, factual behavior belongs in **Reference**; the other three roles link to it rather than duplicating full contracts.

## Current operator path

1. [`README.md`](README.md) for currentness boundaries.
2. [`DOCUMENTATION-INVENTORY.md`](DOCUMENTATION-INVENTORY.md) for lifecycle/ownership.
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`OPERATIONS.md`](OPERATIONS.md) for cross-cutting architecture at their stated subjects.
4. The current Diátaxis set for the capability you operate.
5. Preserved release pages only when you need the historical release subject they name.

For replicated evidence state, read the Tutorial once, then use How-to and Reference operationally. Read Explanation when changing its standing or authority model.

## Preserved v26.8.18 path

The following remain valuable release evidence but are no longer a complete map of current `main` after post-baseline capability merges:

1. [`v26.8.18-release.md`](v26.8.18-release.md)
2. [`ARCHITECTURE.md`](ARCHITECTURE.md)
3. [`OPERATIONS.md`](OPERATIONS.md)
4. [`API-SURFACES.md`](API-SURFACES.md)
5. release-era subsystem pages such as `OBSERVABILITY.md`, `OCEL-PROCESS-EVIDENCE.md`, `GGEN-SERVICE.md`, `SECURITY-MODEL.md`, and `RELIABILITY-AND-DR.md`
6. [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)

Do not infer absence of a post-baseline capability from this historical snapshot.

## Implementer path

Read [`DEVELOPMENT.md`](DEVELOPMENT.md), [`DOCS-MAINTENANCE.md`](DOCS-MAINTENANCE.md), and the owning current Reference page. Then inspect source/tests/workflows for the exact subject before changing a capability claim. Numbered chapters 3–17 cover admission/manufacture/receipt mechanics; chapters 35–43 cover DfCM, authority, security, process, and repository roles.

## Release-verification path

Read [`RELEASE-PROCESS.md`](RELEASE-PROCESS.md), chapters 18–28, then [`v26.9.1/00_CANONICAL_INDEX.md`](v26.9.1/00_CANONICAL_INDEX.md). The v26.9.1 corpus is specification/proof doctrine unless exact runtime evidence accompanies a claim.

## Non-collapse notation

```text
Observed != Admitted != Executed != Verified != Inferred
Proof != Authority
CONSTRUCT != DO
Derivation receipt != Actuation receipt
UNKNOWN != ADMITTED
SpecificationFrozen != ReleaseALIVE
```

The evidence ladder is likewise ordered:

```text
workflow exists < workflow executed < acceptance verified < exact-subject standing
```

Use `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, and typed `REFUSED` literally. A repository may contain a test, workflow, receipt-shaped object, or generated artifact without that object proving the capability described by its name.

## Repositories are coordinates, not the constitution

Implementations such as ggen, ggen-legacy, DfCM, GymAct, AutoFDE, wasm4pm, mfact, OCEL stores, marketplace packs, and replicated-evidence state are replaceable role implementations. For each claim ask which object, admission boundary, verifier, projection, receipt, replay function, closure obligation, and exact subject support it.

## Recurring test

At every layer ask: **Where is the exact receipt?** Then ask whether it is derivation or actuation, whether it binds the exact subject, whether replay/postcondition evidence exists, and whether the documentation role is Tutorial, How-to, Reference, Explanation, or deliberately historical.
