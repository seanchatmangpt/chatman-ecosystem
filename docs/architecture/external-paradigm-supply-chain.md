# External Paradigm Supply Chain

Chatman Ecosystem treats external repositories as **paradigm suppliers**, not
as authorities and not as code to reflexively rewrite.

The purpose of this layer is to outsource discovery of useful engineering
patterns while retaining local control of semantics, admission, authority,
verification, and standing.

## Governing transform

```text
external repository @ exact SHA
        |
        v
RETRIEVE / OBSERVE
        |
        v
extract candidate patterns
        |
        v
normalize to capability semantics
        |
        v
deduplicate against admitted capabilities
        |
        +--> VENDOR  : upstream already owns the mechanism well
        +--> WRAP    : preserve mechanism, replace/strengthen boundary semantics
        +--> REPLACE : preserve donor pattern, use stronger ecosystem machinery
        +--> NOVEL_GAP: no sufficient external semantics exist
        |
        v
falsify / qualify
        |
        v
ggen-marketplace pack
        |
        v
SA2A capability projection
        |
        v
GALL / admission
        |
        v
BRCE for any consequential DO
        |
        v
receipt / replay / standing
```

A supplier never gains authority by being imported. An upstream green build,
release tag, confidence score, popularity signal, or agent recommendation is
evidence about that supplier, not Chatman Ecosystem standing.

## ECC reference supplier

The first registered supplier is `affaan-m/ECC`, pinned in
`upstream/paradigms.json`. ECC is useful because it is already an innovation
concentrator: it maintains a large corpus of skills, agents, commands, hooks,
security patterns, and cross-harness adapters while itself incorporating
patterns from other agent-engineering projects.

The intended relationship is analogous to A2A inside `ash_a2a`: retain the
external protocol/corpus where it is valuable, while replacing governing
semantics with the stronger local model.

## Ownership

- **chatman-ecosystem** owns supplier identity, cross-product classification,
  capability equivalence, admission boundary, and ecosystem standing.
- **ggen-marketplace** owns admitted reusable capability/pattern packs.
- **ggen** owns deterministic manufacture from admitted semantics.
- **ash_a2a / SA2A** owns capability projection and protocol-facing execution
  semantics.
- **sJira** owns work/obligation/checkpoint control graphs.
- **autofde-lab / GymAct** own hypothesis, falsification, repeated trial, and
  qualification.
- **BRCE** owns consequential DO.
- **affidavit / receipts** own evidence, provenance, replay, and standing.
- **external suppliers** own their upstream implementation and releases only.

## Invention rule

```text
invent iff ExistingQualifiedCapabilities does not satisfy RequiredSemantics
```

"Could write it ourselves" is not a novelty proof.

## Update rule

Supplier updates are never consumed from a mutable branch name. A new upstream
SHA creates a new candidate observation. The delta is classified and qualified
before it can replace the previously admitted projection.

This allows upstream communities to keep manufacturing new paradigms while the
Chatman Ecosystem increasingly performs only the smaller job of recognition,
qualification, composition, and lawful adoption.
