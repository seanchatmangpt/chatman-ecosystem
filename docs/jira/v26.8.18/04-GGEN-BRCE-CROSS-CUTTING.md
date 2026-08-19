# BRCE Across ggen IaaS / PaaS / SaaS — v26.8.18

Part of [00-OVERVIEW](00-OVERVIEW.md). The deployment layers change **who consumes the capability**, not the constitutional execution law.

## Invariant

```text
Candidate != Admitted
Proof != Authority
CONSTRUCT != DO
Derivation receipt != Actuation receipt
```

Every consequential transition must factor through the admitted authority/broker path and produce the required receipt. No layer can opt out because it is “managed” or “one click.”

## Layer map

| Layer | Primary constructed object | Consequence boundary | Current v26.8.18 state |
|---|---|---|---|
| IaaS | manufacturing run/capsule | local manufacture/write + receipt/key custody | real, durability/isolation incomplete |
| PaaS | tenant-scoped managed sync request | managed write/fulfillment in tenant workspace | real process-level path, external DO closure incomplete |
| SaaS | buyer purchase/fulfillment intent | buyer-visible fulfillment and optional external deployment | complete commerce path unsupported |

## IaaS

The ggen sync pipeline can construct/write artifacts and emit signed receipt material. That is real manufacture. Infrastructure standing additionally depends on isolation, key identity and receipt custody.

A future isolated capsule must refuse a standing-sensitive run if the platform cannot provide the required admitted key/storage/authority contract. “Run anyway on ephemeral state” can remain a bounded dev mode only when the standing ceiling is explicit.

## PaaS

`POST /provision` is the current real managed crossing. It resolves tenant context, invokes the real binary, tags HTTP origin and records attempts.

Important distinction:

```text
ggen manufacturing receipt
!= proof that an external tenant deployment occurred through BRCE
```

If PaaS later writes into an external repository, cluster, cloud account or production system, that is a new consequential transition requiring explicit authority and an actuation receipt for that subject.

## SaaS

A buyer click has the least ambient authority of all three layers. Purchase/entitlement determines whether fulfillment may begin; it cannot itself be treated as arbitrary deployment authority.

For a pure artifact-delivery product, the primary receipt may be derivation/delivery evidence. For a product that changes the buyer's environment, the final deployment must still pass through BRCE and produce an actuation receipt.

## OCEL complement

OCEL v2 is useful across all layers for process state:

```text
request -> admission -> manufacture -> verification -> fulfillment -> delivery
```

OCEL events describe the process graph. Receipts bind the evidence/authority/consequence identities. An OCEL event saying “deployed” cannot replace the actuation receipt that proves the deployment transition was lawful and observed.

The current repository now has a real OTel -> OCEL accumulation path. That strengthens process evidence, but does not weaken BRCE.

## Trust tiers

Trust-tier checks are an admission mechanism, not authority by themselves. Correct flow:

```text
caller identity
-> entitlement/policy/trust checks
-> admitted candidate
-> authority check for consequence
-> BRCE
```

A trust-tier failure must refuse rather than merely warn if the prohibited operation would otherwise actuate.

## Rail topology

The single current `ggen = PARTIAL_ALIVE` rail is intentionally conservative. A future split can encode different evidence ceilings:

- `ggen_iaas`: isolated manufacture + durable receipt/key custody;
- `ggen_paas`: tenant-scoped managed pipeline + brokered consequence;
- `ggen_saas`: entitlement/purchase/fulfillment/metering + any required external actuation.

The split itself does not raise standing. Each rail needs its own verifier/receipt path.

## Required negative fixtures

A closed layered implementation should prove refusal for:

- missing/invalid tenant identity;
- unauthorized pack/capability tier;
- cross-tenant workspace access;
- missing durable custody when required by the admitted mode;
- tampered receipt;
- post-admission mutation of requested action/input identity;
- buyer purchase attempting an undeclared external deployment;
- model/prompt content attempting to expand authority;
- telemetry/OCEL data attempting to trigger direct execution.

## Standing summary

```text
IaaS manufacturing path: PARTIAL_ALIVE
PaaS managed provisioning path: PARTIAL_ALIVE
SaaS full commerce path: UNSUPPORTED
aggregate current ggen rail: PARTIAL_ALIVE
```

These are not percentages. They are distinct edge closures.

## Falsifier

The layered design fails if any transport or commercial layer can cause a consequential mutation that cannot be traced through the same authority admission -> BRCE -> actuation receipt relation required elsewhere in the ecosystem.

## See also

- [01 — IaaS](01-GGEN-AS-IAAS.md)
- [02 — PaaS](02-GGEN-AS-PAAS.md)
- [03 — SaaS](03-GGEN-AS-SAAS.md)
- [`../../GGEN-SERVICE.md`](../../GGEN-SERVICE.md)
- [`../../OCEL-PROCESS-EVIDENCE.md`](../../OCEL-PROCESS-EVIDENCE.md)
