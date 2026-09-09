# Formal Discovery Factory

Status: **CANDIDATE architecture**. Canonical machine-readable constraints live in `catalog/formal-discovery-loop.toml`. This document is an explanatory projection and does not promote any frontier-mathematics result to `ALIVE`.

## Thesis

The ecosystem does not divide mathematical research into "AI discovery" followed by "formal verification." It treats both as one closed manufacturing loop:

```text
ontology
  -> DfCM option surface
  -> HDDL decomposition
  -> HDIT decision-sufficient projection
  -> typed machine routing
  -> bounded UNKNOWN exploration
  -> ggen manufacture
  -> Lean kernel admission
  -> Lake build/replay
  -> axiom + negative-control audit
  -> mfact certification
  -> admitted ontology delta
  -> next ontology
```

The first half is therefore not a large conversation whose residue is later translated into proof. The first half is ontology-driven search manufacture. The second half is admission and certification. The output of the second half changes the canonical starting state of the next first half.

## 1. Discovery half: ontology is the search substrate

The canonical state is an ontology of mathematical objects, morphisms, constraints, prior art, provenance, failed edges, proof obligations, and standing. Transcripts, prompts, generated Lean files, and summaries are projections or candidates.

DfCM operates on the lawful option graph rather than on prompt variants. A failed proof strategy marks an edge or region `BLOCKED`; it does not imply graph failure. HDDL decomposes a top-level research goal into methods and primitive obligations. HDIT preserves information that changes routing, ranking, repair, proof obligations, or provenance when state is projected into a solver, planner, generator, proof assistant, or human-readable report.

The target invariant is:

```text
UNKNOWN -> candidate -> admitted structure -> reusable machinery
```

Repeated successful cognition is a defect in the architecture if it could instead be represented as ontology, a type, a method, a generator, a verifier, a solver route, or a negative fixture.

## 2. Route known leaves away from general intelligence

The protocol makes routing explicit:

| Problem class | Default machinery |
|---|---|
| ontology/query closure | RDF / SPARQL / SHACL |
| algebra | CAS |
| constraints | SAT / SMT / CP |
| optimization | OR |
| hierarchical planning | HDDL / HTN |
| formal proof | Lean 4 |
| formal dependency build/replay | Lake |
| projection manufacture | ggen |
| formal certification | mfact |
| unresolved semantic transition | LLM candidate production only |

An LLM may search the semantic UNKNOWN frontier. It does not acquire DO authority, theorem standing, ontology-write authority, or permission to replace a known deterministic route merely because it can produce plausible text.

## 3. ggen is the bridge between knowledge and executable search

`ggen` is not limited to generating application source. In this architecture it projects the same admitted knowledge state into the artifacts needed by the current research edge: Lean declarations, fixtures, solver models, HDDL fragments, registry surfaces, audit tables, or other deterministic projections.

The useful abstraction is:

```text
O* --ggen--> projection_i
```

not:

```text
prompt --LLM--> hand-maintained file_i
```

Generated artifacts remain disposable projections. Repairs occur at the owning ontology/template/source boundary and are regenerated.

## 4. Admission half: Lean and Lake are part of the loop, not cleanup

A candidate theorem does not first become "the answer" and then get translated into Lean. Formal candidates are manufactured during research and admitted or refused continuously.

Lean supplies kernel admission under an exact toolchain. Lake supplies the exact build/dependency/replay graph. Axiom audits distinguish a type-checking declaration from its trusted footprint. Negative controls demonstrate that the verifier can refuse corrupted, weakened, sorry-bearing, stale, or otherwise inadmissible subjects.

The architecture therefore distinguishes:

```text
generated != admitted
compiled != axiom-audited
verified once != replay-closed
proof text != exact-subject standing
```

## 5. mfact closes standing

`mfact` is the certification boundary for the formal-mathematics artifact. Its role is not to generate truth. It certifies the relationship among exact subject identity, manufactured projection, kernel admission, build/replay evidence, axiom footprint, negative controls, and release/standing receipts.

The resulting object is not merely `P`. It is closer to:

```text
(P, source, provenance, toolchain, dependencies, axioms, falsifiers, replay, standing)
```

Only the admitted delta returns to canonical ontology. Failed edges return as guards or topology. Informal transcripts do not become canonical knowledge by persistence alone.

## 6. The closed learning equation

For ontology state `O_t`, lawful manufacture `mu`, and admission `alpha`:

```text
C_t       = mu(search(O_t))
DeltaO*_t = alpha(C_t)
O_(t+1)   = O_t union DeltaO*_t union learned_failures_t
```

The economic objective is not maximum token throughput. It is to increase compiled reusable knowledge so that future semantic intelligence demand falls:

```text
d(future repeated semantic reasoning) / d(admitted reusable structure) < 0
```

That is the operational meaning of "the first successful run should make the second run cheaper."

## 7. Frontier-mathematics benchmark and falsifier

This architecture does **not** currently claim that the ecosystem has reproduced a specific frontier result such as the reported Navier-Stokes work. The correct benchmark is an exact-subject experiment.

A qualifying run must record at least:

- the exact mathematical subject and prior-art corpus;
- the ontology and planner identities;
- known leaves routed without LLM use;
- semantic UNKNOWNs actually explored;
- failed edges permanently encoded instead of rediscovered;
- ggen manufacturer identities and artifact digests;
- Lean toolchain and Lake manifest identity;
- kernel admission and axiom audit;
- negative-control receipts;
- mfact certification and independent replay;
- total model tokens, wall time, and semantic recomputation.

The efficiency thesis is falsified for a comparison subject if the closed factory cannot reach independently replayable formal standing with materially less repeated semantic recomputation than the comparison workflow. A failure at one route is topology to learn, not permission to weaken the admission boundary.

## 8. Authority ceiling

The protocol contains `OBSERVE`, `SELECT`, and `CONSTRUCT` stages only. Mathematical search, planning, generation, proof, and certification do not create ambient `DO` authority. Any consequential external action still routes through the ecosystem's brokered authority and receipt laws.

The architecture therefore preserves:

```text
knowledge != capability != authority != execution != standing
planner != authority
generator != authority
proof != external DO authority
```

The success condition is not a larger agent swarm. It is a larger admitted machine whose accumulated structure causes the next frontier problem to require less general intelligence.
