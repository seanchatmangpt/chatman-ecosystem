# Capability Control Plane

`catalog/capabilities.toml` is the canonical v26.9.1 capability graph for repeated decision-manufacturing operations observed across ggen, ggen-marketplace, and ggen-legacy.

The graph preserves the constitutional distinction:

`Capability != Planner != Policy != Role != Agent != Authority`

and the authority classes:

`OBSERVE -> SELECT -> CONSTRUCT -> DO`

A dependency edge means semantic/precondition dependency, not authority inheritance. Capability availability never grants permission. Every `DO` capability is broker-required and receipt-required; merge and branch deletion additionally require their exact authority rather than a stronger-looking neighboring authority.

## Surfaces

Every capability declares the same semantic surface set: CLI, API, MCP, and A2A. These are interface projections of one capability identity, not four independently authored behaviors. The catalog verifier refuses a capability that silently omits one of those semantic surfaces. Surface declaration does not claim that every transport adapter has executable standing yet.

## Public and custom ontology

`ontology/capabilities.ttl` reuses public ontology vocabulary for the concepts that already have public semantics:

- PROV-O for plans/provenance;
- DCTERMS for descriptive metadata;
- SKOS for controlled concept labels;
- ODRL for policy semantics;
- SHACL for admission-shape vocabulary.

The `ce:` namespace contains only the Chatman Ecosystem remainder: capability class, interface, dependency, exact authority requirement, broker/receipt requirement, reversibility, standing, and typed refusal surfaces.

## Executable admission

Run:

```bash
python3 scripts/verify_capabilities.py
python3 -m unittest tests.test_capabilities -v
```

The verifier checks stable identities, allowed standing/authority vocabularies, dependency closure and acyclicity, exact CLI/API/MCP/A2A surface closure, complete input/output/refusal contracts, and the law that every `DO` capability requires both broker admission and a receipt. It also proves `views/generated/capabilities.md` is the deterministic projection of the catalog.

## Current capability families

The catalog now covers exact GitHub observation; branch/PR inventory; standing classification; base-drift detection; current-base recomposition; exact-head workflow observation; failure localization; bounded compatibility repair; source correspondence; vacuity audit; real-ggen deterministic manufacture; replay; ggen-legacy reconstitution; public/custom ontology admission; CLI/API/MCP/A2A projection; authority-ceiling enforcement; exact PR receipts; review readiness; exact-head merge; merged-equivalent branch retirement; typed blocker standing; and WIP-train consolidation.

## Standing ceiling

The new catalog entries begin at `CANDIDATE`. Their definitions and negative courts may be admitted by the exact-head capability workflow, but an individual capability must not be promoted to `ALIVE` merely because its catalog row exists. `ALIVE` still requires observed execution against the exact admitted subject under the owning verifier and receipt/replay boundary.

Live Azure remains `BLOCKED:LIVE_AZURE_AUTHORITY` unless separately granted exact named authority. WW3Gym remains simulation/evaluation-only. BRCE remains the exclusive consequential DO path unless narrower owning doctrine proves otherwise.
