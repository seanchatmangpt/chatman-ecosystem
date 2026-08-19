# 68. Build the Canonical Product

## Begin with the product, not the first vendor form

The end-to-end build starts by manufacturing the canonical commercial subject before touching AWS, Microsoft, Google, Oracle, SAP, Salesforce, or any other marketplace console.

The input is the real platform: capabilities, deployment modes, operational limits, security controls, support boundaries, cost model, existing customers, and evidence. That observation set is partial. Some desirable claims may not yet be true. The first task is to preserve the difference.

```text
Observed capability != promised capability
Implemented capability != qualified capability
Qualified capability != commercially offered capability
```

## Step 1 — resolve exact product identity

Create stable identities for the commercial product and its first product version. Bind the version to the runtime/artifact subjects that can actually be fulfilled.

```text
CommercialProduct
ProductVersion
source/runtime identities
release/evidence identities
```

Do not use a display name, container tag, marketplace SKU, or repository branch as the durable commercial identity.

## Step 2 — inventory capabilities

For every candidate capability, record:

```text
capability id
customer meaning
implementation subject
current standing
security/data implications
supported deployment classes
support ownership
known exclusions
next falsifier
```

A feature that exists in source but has never been executed remains bounded accordingly. The canonical graph can contain it as `CANDIDATE` without putting it into a sellable plan.

## Step 3 — define plans as rights

A plan is not a pricing-page label. It is an admitted set of capabilities, quantities, limits, support, and lifecycle semantics.

```text
Plan = Rights + Quantities + Support + LifecyclePolicy
```

Separate public plan semantics from buyer-scoped negotiated deltas. This makes private offers possible without forking the product.

## Step 4 — define meters and prices

For each usage-priced dimension, define the measurement system before the price. Bind unit, observation source, precision, aggregation, window, correction policy, and evidence.

Price versions then reference these meters and commercial terms. Historical agreements retain the price/meter versions they accepted.

## Step 5 — define fulfillment classes

At minimum classify the supported product delivery modes:

- vendor-hosted SaaS;
- customer-hosted Kubernetes or infrastructure;
- managed application;
- container/operator package;
- API consumption;
- data/AI product where applicable;
- professional or managed service where applicable.

Each class declares target identity, operational owner, data boundary, security/network requirements, customer inputs, postcondition verifier, compensation, and teardown.

## Step 6 — bind enterprise promises

Add support policy, SLO/SLA candidates, security claims, data-residency capabilities, identity/federation support, private connectivity, DR, upgrade policy, and legal-artifact references.

Claims are admitted only at the scope their evidence supports.

## Step 7 — admit the graph

Run ontology/SHACL/schema constraints, product invariants, exact-source correspondence, and policy checks. The output is an admitted graph suitable for manufacture:

```text
G_c* = admit(G_c_candidate)
```

Admission still provides no marketplace publication or financial DO authority.

## Refusals

- `REFUSED:AWS_FIELDS_AS_PRODUCT_MODEL`
- `REFUSED:SOURCE_EXISTS_AS_CUSTOMER_PROMISE`
- `REFUSED:DISPLAY_STRING_AS_STABLE_IDENTITY`
- `REFUSED:PLAN_WITH_UNDEFINED_TERMINATION`
- `REFUSED:METER_PRICE_WITHOUT_MEASUREMENT_SEMANTICS`
- `REFUSED:SECURITY_CLAIM_BEYOND_EVIDENCE`

## Operational exercise

Produce the complete canonical graph for the running platform: product/version, capabilities, two plans, one buyer-scoped delta, one usage meter, three fulfillment classes, security/support/data policies, and exact standing. The graph must validate without containing a single marketplace-specific product ID.
