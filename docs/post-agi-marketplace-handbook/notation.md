# Notation and Commercial Calculus

## Core equation

```text
A = μ(O*)
R = receipt(A)
```

`O` is candidate observation. `O*` is the bounded, aligned, grounded, admitted observation. `μ` is lawful manufacture. `A` is an artifact or action result with a precisely scoped standing claim. `R` binds the consequence to evidence.

## Canonical product graph

```text
G_c = (V, E, C, P)
```

`V` are commercial objects: product, plan, offer, agreement, entitlement, usage, fulfillment, support, evidence. `E` are typed relations. `C` are constraints. `P` is provenance.

## Marketplace projection

```text
C_m = π_m(G_c)
```

`π_m` is a marketplace-specific projection. It may add vendor extension nodes and may expose only a subset of the canonical graph. Projection loss must be explicit.

## Admission

```text
O* = admit(O, identity, authority, constraints, freshness)
```

Admission never creates ambient DO authority. It establishes which facts may participate in construction.

## Entitlement transition

```text
E_{t+1} = δ(E_t, event, idempotency_key)
```

The transition uses effective time and source provenance. A delayed event cannot simply be applied in arrival order.

## Fulfillment

```text
(ServiceState, R_f) = μ_f(E*, Target*, Authority*)
```

Entitlement is a prerequisite to fulfillment, not proof that fulfillment succeeded.

## Metering

```text
UsageBatch = aggregate(normalize(ObservedUsageEvents), admitted_window)
```

The vendor submission is a projection of a measured batch; the vendor API response does not manufacture the underlying usage.

## BRCE

```text
Intent = CONSTRUCT(O*)
(Consequence, R) = Broker.DO(Intent, ExactAuthority)
Verify(Consequence, ExpectedPostcondition)
```

Replay verifies evidence without repeating the consequence.

## Standing

```text
Standing(subject, capability) =
  f(identity, execution, verification, receipt, replay, exclusions)
```

Standing is capability-specific and exact-subject-specific. It does not automatically transfer between versions, marketplaces, environments, or adjacent capabilities.

## Commercial invariance

For canonical invariant `I` and admitted projection `π_m`:

```text
I(G_c) = I(normalize(π_m(G_c)))
```

where the invariant is applicable. If a marketplace cannot represent the invariant, the result is a typed gap, not a false equivalence.

## Symbols

| Symbol | Meaning |
|---|---|
| `O` | candidate observation |
| `O*` | admitted observation |
| `μ` | lawful manufacture |
| `π_m` | projection into marketplace `m` |
| `G_c` | canonical commercial product graph |
| `E` | entitlement state |
| `δ` | lifecycle transition |
| `A` | artifact/action result |
| `R` | receipt |
| `S` | standing |
| `BRCE` | bounded, receipted, controlled execution |
