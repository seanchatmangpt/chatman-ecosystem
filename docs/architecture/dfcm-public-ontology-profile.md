# DfCM public-ontology application profile

## Subject

Design for Combinatorial Maximalism (DfCM) is represented as a thin application profile over public ontologies. The canonical machine-readable contract is `catalog/dfcm.toml`; `ontology/dfcm.ttl` defines only the irreducible semantic remainder and `ontology/dfcm.shacl.ttl` defines the admission membrane.

## Calculus

`lawful_options = options ∩ ontology ∩ capability ∩ authority ∩ cost ∩ evidence ∩ consequence`

Before an irreversible selection, preserve the maximum lawful reversible frontier. One failed edge changes the topology; it does not invalidate unrelated lawful options.

The `SOLVE(x)` order is fixed:

`PRESERVE → FENCE → CALCULUS → EXCLUSIONS → FALSIFIER → EXTENSION → OPERATIONALIZE`

Extension order is `reuse → compose → extend → invent`; invention is admitted only after an exact falsifier shows that the public/established form cannot satisfy required semantics.

## Public ontology fence

| Concern | Public vocabulary |
| --- | --- |
| provenance/execution | PROV-O |
| plans/steps | P-Plan |
| admission | SHACL |
| authority/policy | ODRL + ORG |
| observations | SOSA/SSN |
| verification | EARL |
| contextual standing | SKOS |
| time | OWL-Time |
| catalog/metadata | DCAT + DCTERMS |
| quality/measurements | DQV + QUDT |
| software identity | SPDX |

The local `dfcm:` namespace does not redefine public terms. It contains only decision-frontier intersection semantics not supplied by those vocabularies.

## Authority and standing

SHACL conformance is admission evidence, not execution and not `ALIVE`. Plans, proofs, hooks, credentials, and capability do not grant authority. Consequential DO remains exclusively behind BRCE and requires its own exact authority and receipt.

Standing remains contextual: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, or typed `REFUSED`. `ALIVE` requires observed execution of the exact admitted subject with independent verification and replayable receipt evidence.

## Replay

Narrow profile verification:

```bash
python3 scripts/verify_dfcm_profile.py
python3 -m unittest tests.test_dfcm_profile -v
```

Repository Crown remains separate and must be evaluated by the existing `./scripts/crown.sh` path. Passing this profile verifier does not promote repository Crown standing.
