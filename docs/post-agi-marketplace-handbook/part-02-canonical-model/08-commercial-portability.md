# 8. Commercial Portability

## Run anywhere is weaker than sell anywhere

Technical portability asks whether software can execute across environments. Commercial portability asks whether product identity and customer meaning survive different procurement, entitlement, fulfillment, metering, settlement, support, and governance protocols.

A container that runs on AWS, Azure, Google Cloud, and OCI is technically portable. If each marketplace requires a different manually maintained plan model and those plans grant subtly different rights, the product is not commercially portable.

```text
C_m = π_m(G_c)
```

`G_c` is the canonical commercial graph. `π_m` projects it into marketplace `m`. The projection is admitted when required invariants survive normalization back into canonical semantics.

## Invariants and permitted differences

Typical invariants include:

- canonical product/version identity;
- feature and quantity rights granted by a plan;
- support promises;
- security claims;
- metering meaning and unit;
- termination semantics;
- evidence requirements.

Permitted projection differences can include:

- vendor listing IDs;
- offer creation protocol;
- settlement cadence;
- supported term lengths;
- package format;
- partner program metadata;
- marketplace-specific private-offer features;
- customer-resolution protocol.

A difference is not a defect when it is represented.

## Avoid lowest-common-denominator architecture

Commercial portability does not require shrinking every product to the intersection of vendor capabilities. That would discard lawful value. Instead:

```text
Core(B) = intersection of required invariant semantics
Extensions(B) = admitted vendor-specific capabilities
Gaps(B) = explicit unsupported or blocked edges
```

A marketplace that cannot express a rich contract amendment may still sell the product under a simpler offer class. A data marketplace may expose usage semantics that have no direct equivalent in an application marketplace. Those facts remain projections rather than reasons to corrupt the core.

## Projection loss is evidence

Every mapping should classify loss:

- `EQUIVALENT` — canonical and vendor meanings are aligned within the bound;
- `NARROWER` — the vendor represents a subset;
- `BROADER` — vendor primitive includes extra semantics;
- `LOSSY` — some canonical meaning cannot be represented;
- `EXTENSION` — vendor introduces an additional semantic;
- `UNSUPPORTED` — no admissible projection exists;
- `UNKNOWN` — equivalence has not been established.

This makes a capability matrix useful as architecture rather than marketing.

## One failed market is topology

If a GCP packaging validator rejects a required Kubernetes resource for structural reasons, that edge can be BLOCKED while SaaS entitlement remains independently qualifiable. If a ServiceNow Store projection requires a scoped application, that does not invalidate the SaaS product. Commercial standing is a matrix, not one global boolean.

## Falsifier

Commercial portability is falsified when two marketplace purchases mapped to the same canonical plan result in materially different customer rights and the graph contains no explicit projection difference that explains it.

## Operational exercise

Compare two marketplaces across product identity, public offer, private offer, agreement, entitlement, metering, fulfillment, amendment, support, and termination. Classify each mapping with the projection vocabulary above. Do not use “basically the same” as a type.
