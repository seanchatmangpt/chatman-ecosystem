# ggen as PaaS — v26.8.18 Observed State

Part of [00-OVERVIEW](00-OVERVIEW.md). The PaaS proposal is now partially realized and must no longer be described as a health/status stub.

## Standing

`PARTIAL_ALIVE`

A real API-driven ggen sync/provisioning path exists and has been deployed/live-observed. Tenant scoping, attempt logging, real receipt output, and marketplace registry access exist. Durable standing state and the complete brokered external deployment path remain open.

## Managed capability

PaaS means the caller requests semantic manufacture without owning the local ggen toolchain lifecycle. The platform owns:

- real ggen binary invocation;
- run workspace creation;
- pack installation;
- sync execution;
- signing-key selection;
- receipt retrieval/verification;
- tenant namespace/workspace resolution;
- attempt logging;
- explicit failure when the real dependency is unavailable.

The caller still supplies semantic inputs such as ontology and pack requests. That distinguishes PaaS from the higher SaaS purchase/entitlement layer.

## Real `/provision` path

`platform-console/services/ggen/app.py` implements `POST /provision` using the real ggen CLI through subprocess execution. The observed path performs initialization/materialization, pack installation, sync, receipt collection and receipt verification.

The service requires a project/tenant context, resolves a Kubernetes namespace, places execution under a tenant-scoped workspace, tags the HTTP result with the PaaS origin, and logs attempts whether applied or failed/refused.

Later v26.8.18 session evidence rebuilt/redeployed the `ggen-status:v26.8.18-live` image and confirmed the live pod responding on its health/status surface. This supersedes earlier ticket text that said live-cluster status was unverified.

## Marketplace-as-a-service

The ggen-marketplace service is also no longer a health-only stub. Its real registry/query bridge exposes marketplace metadata and returned **151 pack records** at the observed point.

This closes the earlier “no HTTP pack registry” gap at the generic metadata/query level. Remaining semantic gap: the bridge does not make all pack-specific domain ontology triples available as one complete public semantic graph.

## One capability, multiple projections

CLI, MCP and HTTP should route to shared semantic functions rather than duplicate business logic. The existing shared pack-query precedent remains the design rule:

```text
capability semantics
  -> CLI projection
  -> MCP projection
  -> HTTP/PaaS projection
```

Projection does not create new authority. Mutation still requires the owning admission/BRCE contract.

## Unattended behavior

The ecosystem already has bounded unattended-write patterns in ggen. A managed PaaS may automate eligible work, but automation must remain:

- explicitly eligible;
- bounded to declared write classes;
- fail-closed;
- receipted;
- logged on attempts, not only success;
- incapable of expanding authority from prompt/model content.

The v26.8.18 HTTP service implements origin/attempt semantics but does not by itself prove the final external `DO` path for every generated artifact.

## Remaining gaps

1. **Durability:** receipt/attempt/key state that matters for standing must survive service replacement.
2. **Per-tenant capsule isolation:** workspace/namespace scoping is weaker than independently isolated runtime/key/storage boundaries.
3. **Signed origin correspondence:** HTTP origin metadata is not automatically bound into the ggen receipt bytes.
4. **External actuation closure:** manufacturing files is not the same as deploying them into an external tenant environment through BRCE.
5. **Semantic marketplace completeness:** generic 151-record metadata bridge is not full domain-ontology closure.
6. **Layered standing:** one `ggen = PARTIAL_ALIVE` rail still conflates IaaS/PaaS/SaaS evidence ceilings.

## Rail status

`catalog/rails.toml` contains one `ggen` rail at `PARTIAL_ALIVE`, citing the service and this work package. A future per-layer split is preferable when independent evidence exists:

```text
ggen_iaas
ggen_paas
ggen_saas
```

Do not split rails solely to improve narrative granularity; each new rail needs an executable verifier/evidence path.

## See also

- [01 — ggen as IaaS](01-GGEN-AS-IAAS.md)
- [03 — ggen as SaaS](03-GGEN-AS-SAAS.md)
- [04 — BRCE cross-cutting](04-GGEN-BRCE-CROSS-CUTTING.md)
- [`../../GGEN-SERVICE.md`](../../GGEN-SERVICE.md)
