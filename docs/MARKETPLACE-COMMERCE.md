# Marketplace Commerce — Commercial Standing v26.8.19

## Standing

`PARTIAL_ALIVE` is the maximum claim for this change: the canonical commerce kernel, provider normalization, negative fixtures, receipt chaining, and replay are executable software. Live Fortune-5 payment acceptance remains `BLOCKED` until real marketplace seller enrollment, tax/payout profiles, provider credentials, contractual production commitments, independent compliance evidence, and live buyer/meter/settlement receipts exist.

Executable fixture closure is not live commercial standing.

## Commercial invariant

```text
marketplace observation
→ exact buyer / product / agreement binding
→ entitlement
→ fulfillment admission
→ manufacture receipt
→ delivery receipt
→ usage derived from fulfillment
→ provider meter acknowledgement
→ settlement reconciliation
→ credit / refund adjustment
→ replay
```

The laws are:

- zero unentitled fulfillment;
- zero unreceipted commercial transitions;
- zero metering that diverges from receipted usage;
- zero settlement that diverges from admitted price, units, or currency;
- zero cross-provider or cross-buyer identity collapse;
- zero duplicate financial actuation under conflicting idempotency semantics.

## Executable surface

Canonical source: `crates/ecosystem-runtime/src/commerce.rs`.

Executable verifier: `crates/ecosystem-runtime/src/bin/marketplace-commerce.rs`.

```bash
cargo run --locked --quiet -p ecosystem-runtime --bin marketplace-commerce -- verify-fixtures
```

The verifier executes the same commercial lifecycle for AWS Marketplace, Microsoft Marketplace, and Google Cloud Marketplace projections: agreement observation, entitlement, plan/quantity change, fulfillment authorization, manufacture/delivery binding, usage, meter acceptance, settlement, credit/refund, idempotent replay, identity tamper refusal, wrong-authority refusal, suspension/reinstatement/revocation, and post-revocation refusal.

Provider observations can be normalized independently:

```bash
cargo run --locked --quiet -p ecosystem-runtime --bin marketplace-commerce -- normalize aws agreement < aws.json
cargo run --locked --quiet -p ecosystem-runtime --bin marketplace-commerce -- normalize microsoft entitlement < microsoft.json
cargo run --locked --quiet -p ecosystem-runtime --bin marketplace-commerce -- normalize google meter-accepted < google.json
```

Normalization is SELECT/CONSTRUCT only. It performs no provider mutation and grants no ambient `DO` authority.

## Canonical graph

`ontology/marketplace-commerce.ttl` is the public ontology; `ontology/marketplace-commerce.shacl.ttl` defines structural admission shapes. The graph keeps these identities distinct:

```text
Seller → Marketplace → Buyer → Product → SKU → Offer → Order → Agreement
                                                     ↓
                                              Subscription
                                                     ↓
                                                Entitlement
                                                     ↓
                                                Fulfillment
                                                     ↓
                                                  Artifact
                                                     ↓
                                                 UsageEvent
                                                     ↓
                                                 MeterEvent
                                                     ↓
                                                Settlement
                                               ↙          ↘
                                            Credit       Refund
```

Every consequential transition is represented by a BLAKE3-sealed core `Receipt` and chained to the preceding commercial receipt. Provider IDs are projections onto this graph, never replacements for internal identities.

## Provider projections

### AWS Marketplace

The normalizer requires `CustomerAWSAccountId`, `LicenseArn`, and `ProductCode` for the admitted identity. Agreement, entitlement, meter acknowledgement, and settlement observations map into the same canonical state machine without collapsing buyer account and license identities.

### Microsoft Marketplace

The normalizer preserves marketplace subscription identity independently from purchaser/beneficiary tenant identity and offer/plan. Subscription lifecycle events map to entitlement admission/change/suspend/reinstate/revoke.

### Google Cloud Marketplace

The normalizer preserves procurement account, entitlement resource, product, plan, and usage event identities independently before admission.

## Authority

The kernel preserves the existing constitutional authority classes:

- observation and internal persistence: `PersistControlPlane`;
- fulfillment and entitlement consequence: `ModifyExternalObject`;
- metering, credit, and refund: `Spend`.

Wrong authority is a typed refusal. Provider payloads themselves never receive authority.

## Explicit external blockers

| Requirement | Standing | Promotion evidence |
|---|---|---|
| AWS seller/product enrollment | `UNKNOWN/BLOCKED` | authenticated seller account, accepted product, live test agreement |
| Microsoft seller/offer enrollment | `UNKNOWN/BLOCKED` | authenticated publisher, transactable offer, live resolved subscription |
| Google Cloud vendor/product enrollment | `UNKNOWN/BLOCKED` | vendor account, approved product, live procurement entitlement |
| Tax profile | `BLOCKED` | provider-accepted legal tax profile |
| Payout profile | `BLOCKED` | provider-accepted payout destination |
| Fortune-5 contractual SLA | `BLOCKED` | executed customer agreement/SLA with remedies |
| SOC 2 attestation | `BLOCKED` | independent auditor opinion |
| Production HA/DR | `BLOCKED` | executed multi-AZ/multi-region failure and recovery receipts |
| Live metering/settlement | `BLOCKED` | provider-accepted meter and settlement tied to the exact receipt DAG |

No fixture, ontology triple, CI result, source file, or synthetic payload may promote those external facts to `ALIVE`.

## Crown path

`scripts/crown.sh` executes `marketplace-commerce verify-fixtures` before Crown admission evidence is manufactured. `.github/workflows/marketplace-commerce.yml` executes exact-head formatting, clippy, tests, executable fixtures, and schema validation on pull requests and main.

Promotion to live `MARKETPLACE_ALIVE` requires a real buyer fixture for each admitted provider:

```text
purchase
→ provider identity resolution
→ entitlement
→ fulfillment
→ artifact / DO receipt
→ usage
→ provider meter acceptance
→ billing/settlement observation
→ reconciliation
→ cancellation/revocation refusal
→ replay
```

Seller enrollment, customer risk acceptance, spend authority, contract approval, and production release remain separate authority classes.
