# Capability Control Plane

`catalog/capabilities.toml` is the canonical v26.9.1 capability graph for repeated decision-manufacturing operations observed across ggen, ggen-marketplace, and ggen-legacy.

The graph preserves the constitutional distinction:

`Capability != Planner != Policy != Role != Agent != Authority`

and the authority classes:

`OBSERVE -> SELECT -> CONSTRUCT -> DO`

A dependency edge means semantic/precondition dependency, not authority inheritance. Capability availability never grants permission. Every `DO` capability is broker-required and receipt-required; merge and branch deletion additionally require their exact authority rather than a stronger-looking neighboring authority.

## Surfaces

Every capability declares the same semantic surface set: CLI, API, MCP, and A2A. These are interface projections of one capability identity, not four independently authored behaviors. The catalog verifier refuses a capability that silently omits one of those semantic surfaces.

`scripts/capability_control.py` is the executable, read-only projection kernel. It loads and verifies the canonical catalog on every invocation and can emit the same capability contract as CLI, API, MCP, or A2A metadata. It does not actuate the projected capability. A protocol surface therefore cannot create authority that is absent from the catalog.

The Rust control-plane CLI exposes this kernel directly:

```bash
ecosystem capability list
ecosystem capability show capability:observe-exact-github-subject
ecosystem capability graph
ecosystem capability surface cli
ecosystem capability surface api
ecosystem capability surface mcp
ecosystem capability surface a2a
```

The API and A2A projections are contract surfaces, not claims that an HTTP or A2A server has executed. The MCP projection is likewise descriptive; consequential MCP mutations remain refused at the existing broker boundary. The CLI transport has an executable black-box court in `apps/ecosystem-cli/tests/capabilities.rs`.

## DfCM execution

The same kernel computes a reversible dependency-closed frontier instead of prematurely choosing one implementation edge:

```bash
ecosystem capability dfcm \
  --state /tmp/capability-standing.json \
  --authority observe \
  --authority classify \
  --authority persist_control_plane \
  --authority draft
```

State input is explicit observation:

```json
{
  "standing": {
    "capability:observe-exact-github-subject": "ALIVE"
  }
}
```

Rules are fail-closed:

- an unobserved dependency is `UNKNOWN`, never implicitly ALIVE;
- every dependency must be explicitly ALIVE before its dependent edge enters the executable frontier;
- exact authority must be supplied for the candidate capability;
- `DO` is excluded by default even when other dependencies are ALIVE;
- `--include-do` still cannot admit DO without its exact authority, `broker_required = true`, and `receipt_required = true`;
- DfCM returns the maximal currently lawful frontier and performs no selection or consequential actuation.

This preserves combinatorial optionality while keeping irreversible transitions fenced.

## Public and custom ontology

`ontology/capabilities.ttl` reuses public ontology vocabulary for the concepts that already have public semantics:

- PROV-O for plans/provenance;
- DCTERMS for descriptive metadata;
- SKOS for controlled concept labels;
- ODRL for policy semantics;
- SHACL for admission-shape vocabulary.

The `ce:` namespace contains only the Chatman Ecosystem remainder: capability class, interface, dependency, exact authority requirement, broker/receipt requirement, reversibility, standing, and typed refusal surfaces.

Public ontology terms are alignment vocabulary, not ambient authority. The custom graph does not redefine public concepts simply because a local implementation uses them.

## Executable admission

Replay the capability source and deterministic projection:

```bash
python3 scripts/verify_capabilities.py
python3 -m unittest tests.test_capabilities tests.test_capability_control -v
python3 scripts/capability_control.py list
python3 scripts/capability_control.py graph
for surface in cli api mcp a2a; do
  python3 scripts/capability_control.py surface "$surface"
done
```

The verifier checks stable identities, allowed standing/authority vocabularies, dependency closure and acyclicity, exact CLI/API/MCP/A2A surface closure, complete input/output/refusal contracts, and the law that every `DO` capability requires both broker admission and a receipt. It also proves `views/generated/capabilities.md` is the deterministic projection of the catalog.

The DfCM/refusal court proves surface semantic equivalence, no authority-from-surface promotion, maximal reversible root preservation, dependency gating, default DO refusal, exact-authority refusal, and no-actuation output.

## Current capability families

The catalog covers exact GitHub observation; branch/PR inventory; standing classification; base-drift detection; current-base recomposition; exact-head workflow observation; failure localization; bounded compatibility repair; source correspondence; vacuity audit; real-ggen deterministic manufacture; replay; ggen-legacy reconstitution; public/custom ontology admission; CLI/API/MCP/A2A projection; authority-ceiling enforcement; exact PR receipts; review readiness; exact-head merge; merged-equivalent branch retirement; typed blocker standing; and WIP-train consolidation.

## Standing ceiling

Catalog rows begin at `CANDIDATE`. Definitions, projections, DfCM decisions, and refusal courts may be admitted by the exact-head capability workflow, but an individual operational capability must not be promoted to `ALIVE` merely because its contract exists.

`ALIVE` still requires observed execution against the exact admitted subject under the owning verifier and receipt/replay boundary. Contract-only API/A2A projection is therefore not API/A2A runtime standing. A named MCP contract is not consequential MCP authority. A merge capability is not merge authorization.

Live Azure remains `BLOCKED:LIVE_AZURE_AUTHORITY` unless separately granted exact named authority. WW3Gym remains simulation/evaluation-only. BRCE remains the exclusive consequential DO path unless narrower owning doctrine proves otherwise.
