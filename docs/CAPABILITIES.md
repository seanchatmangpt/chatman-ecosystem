# Capability Control Plane

The v26.9.1 decision-manufacturing graph has two canonical source catalogs:

- `catalog/capabilities.toml` — 22 repository-control/reconstitution capabilities;
- `catalog/capabilities-decision-graph.toml` — 17 ownership-bounded ecosystem capabilities.

Together they form one dependency-closed graph of **39 capabilities**. `catalog/repositories.toml` is the canonical owner registry; capability admission refuses an owner not declared there. Repository registration is identity/role evidence only and does not promote a repository to runtime `ALIVE`.

The graph preserves the constitutional distinction:

`Capability != Planner != Policy != Role != Agent != Authority`

and the authority classes:

`OBSERVE -> SELECT -> CONSTRUCT -> DO`

A dependency edge means semantic/precondition dependency, not authority inheritance. Capability availability never grants permission. Every `DO` capability is broker-required and receipt-required; merge and branch deletion additionally require their exact authority rather than a stronger-looking neighboring authority.

## Ownership graph

The extension makes the ecosystem boundaries executable catalog law:

- **AutoFDE Lab** owns planning, reversible frontier construction, falsification, and capability-plan admission.
- **BCINR** owns bounded CMCA.
- **MFW** owns manufacturing-work orchestration.
- **ggen** owns deterministic manufacture.
- **ggen-marketplace** owns qualified executable-knowledge distribution.
- **dsrust** is an optional bounded compiler/oracle; its output is neither proof nor authority.
- **GymAct** owns executable worlds; domain gyms consume that world contract.
- **RRgym, LifeGym, BibleGym and other domain gyms** remain bounded evaluation worlds.
- **WW3Gym** is explicitly fenced to simulation/evaluation and receives no real-world authority.
- **AutoFDE** owns persistent runtime state and the BRCE consequential boundary.
- **Affidavit** owns evidence/standing attestation only; it cannot manufacture DO authority.
- **ggen-legacy** owns bounded predecessor/project reconstitution, including public/custom ontology and protocol-surface correspondence.
- **Chatman Ecosystem** owns cross-repository identity, standing, authority ceilings, exact-subject evidence, and the composition graph.

## Surfaces

Every capability declares the same semantic surface set: CLI, API, MCP, and A2A. These are interface projections of one capability identity, not four independently authored behaviors. The catalog verifier refuses a capability that silently omits one of those semantic surfaces.

`scripts/capability_control.py` is the executable read-only projection kernel. It verifies the complete canonical graph on every invocation and emits the same capability contract as CLI, API, MCP, or A2A metadata. It never actuates the projected capability, so a protocol surface cannot create authority absent from the catalog.

The Rust control-plane CLI exposes the kernel:

```bash
ecosystem capability list
ecosystem capability show capability:observe-exact-github-subject
ecosystem capability graph
ecosystem capability surface cli
ecosystem capability surface api
ecosystem capability surface mcp
ecosystem capability surface a2a
```

The CLI transport has a black-box process court. API, MCP and A2A projections are semantic contracts unless their owning transport is independently executed; contract existence is never promoted to transport `ALIVE`. Consequential MCP mutations remain refused at the existing broker boundary.

## DfCM execution

The same kernel computes the maximal reversible dependency-closed frontier instead of prematurely choosing one implementation edge:

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
- `DO` is excluded by default even when every dependency is ALIVE;
- `--include-do` still cannot admit DO without its exact authority, `broker_required = true`, and `receipt_required = true`;
- DfCM returns the maximal currently lawful frontier and performs no selection or consequential actuation.

This preserves combinatorial optionality while keeping irreversible transitions fenced.

## Public and custom ontology

`ontology/capabilities.ttl` reuses public vocabulary where public semantics already exist:

- PROV-O for provenance, plans, agents and activities;
- DCTERMS for descriptive metadata;
- SKOS for controlled concepts;
- ODRL for policy semantics;
- SHACL for admission-shape vocabulary.

The `ce:` namespace contains only the Chatman Ecosystem remainder: capability classes/interfaces/dependencies, planner-policy-role-agent-authority separation, exact authority requirements, repository ownership, BRCE semantics, broker/receipt requirements, standing, live-Azure fencing and typed refusals.

`scripts/verify_capability_ontology.py` mechanically verifies those namespace identities and alignment fences. It explicitly does **not** claim SHACL runtime execution; SHACL standing requires an independent SHACL engine execution against the exact subject.

## Executable admission and replay

```bash
python3 scripts/verify_capabilities.py
python3 scripts/verify_capability_ontology.py
python3 -m unittest \
  tests.test_capabilities \
  tests.test_capability_control \
  tests.test_capability_ontology -v
python3 scripts/capability_control.py list
python3 scripts/capability_control.py graph
for surface in cli api mcp a2a; do
  python3 scripts/capability_control.py surface "$surface"
done
```

`python3 scripts/verify_capabilities.py --write` manufactures both generated capability Markdown projections; admission requires the second manufacture to be byte-identical. The ordinary ecosystem projection court separately binds `catalog/repositories.toml` to `views/generated/portfolio.md`.

The capability court proves stable identities, 39-node dependency closure and acyclicity, declared repository ownership, exact CLI/API/MCP/A2A semantic closure, complete input/output/refusal contracts, DO broker/receipt law, public/custom namespace fencing, DfCM dependency gating, default DO refusal, exact-authority refusal, and no-actuation output.

## Reconstitution closure

`capability:reconstitute-project-protocol-suite` is the common closure operation for ecosystem repositories:

`exact subject + public ontology + custom remainder + observed interfaces -> O -> O* -> ggen-legacy -> reconstituted capability graph -> CLI/API/MCP/A2A projections -> receipts/replay`

It does not claim that every repository has already completed that execution. Per-project `ALIVE` remains owned by the exact repository subject and its real reconstitution verifier.

## Standing ceiling

Catalog rows begin at `CANDIDATE` unless a fence itself is explicitly `BLOCKED`. Definitions, projections, DfCM decisions, and refusal courts may be admitted by the exact-head capability workflow, but an operational capability is never `ALIVE` merely because its contract exists.

`ALIVE` still requires observed execution against the exact admitted subject under the owning verifier and receipt/replay boundary. A contract-only API/A2A projection is not API/A2A runtime standing. A named MCP contract is not consequential MCP authority. A merge capability is not merge authorization.

Live Azure remains `BLOCKED:LIVE_AZURE_AUTHORITY` unless separately granted exact named allowlisted authority. WW3Gym remains simulation/evaluation-only. BRCE remains the exclusive consequential DO path unless narrower owning doctrine proves otherwise.
