# Marketplace Commerce — Commercial Standing v26.8.19

## Standing

`PARTIAL_ALIVE` is the maximum code-level claim for this work. The canonical commerce kernel, provider normalization, provider-authenticated lifecycle ingress, buyer-to-tenant binding, entitlement actuation, receipt-gated metering, durable idempotency, and replay/refusal fixtures are implemented. Live Fortune-5 payment acceptance remains `BLOCKED` until real seller enrollment, tax/payout profiles, provider credentials, approved offers, live buyer purchases, provider-accepted usage, settlement evidence, production SLA/HA/DR, and independent compliance evidence exist.

Executable fixtures are not live commercial standing.

## Commercial invariant

```text
marketplace observation
→ provider authentication
→ exact buyer/product/agreement binding
→ entitlement
→ local tier/access actuation
→ provider acknowledgement
→ fulfillment receipt
→ usage derived from trusted receipt custody
→ provider meter acknowledgement
→ settlement/reconciliation
→ credit/refund
→ replay
```

The laws are:

- zero unentitled fulfillment;
- zero unreceipted commercial transitions;
- zero metering without a source receipt already present in trusted custody;
- zero metering that diverges from admitted buyer/agreement/subscription identity;
- zero settlement that diverges from admitted price, units, or currency;
- zero cross-provider or cross-buyer identity collapse;
- zero duplicate financial actuation under conflicting idempotency semantics.

## Constitutional verifier

Canonical Rust source: `crates/ecosystem-runtime/src/commerce.rs`.

Executable verifier: `crates/ecosystem-runtime/src/bin/marketplace-commerce.rs`.

```bash
cargo run --locked --quiet -p ecosystem-runtime --bin marketplace-commerce -- verify-fixtures
```

The verifier executes the same commercial lifecycle for AWS Marketplace, Microsoft Marketplace, and Google Cloud Marketplace projections. It covers agreement observation, entitlement, plan/quantity change, fulfillment authorization, manufacture/delivery binding, usage, meter acceptance, settlement, credit/refund, idempotent replay, identity-tamper refusal, wrong-authority refusal, suspension/reinstatement/revocation, and post-revocation refusal.

## Operational runtime

`platform-console/app/lib/marketplace-runtime.ts` is the non-generated provider/runtime integration layer. The generated `lib/entitlement-adapters/{aws,azure,gcp}.ts` files remain generated projections and are not hand-edited.

The operational rail exposes three dynamic provider surfaces:

```text
POST /api/marketplace/{aws|azure|gcp}/register
POST /api/marketplace/{aws|azure|gcp}/webhook
POST /api/marketplace/{aws|azure|gcp}/usage
```

`register` remains behind normal owner/session or API-key authorization. It resolves the provider purchase identity, verifies the target Project/namespace, persists a non-overwritable provider→tenant binding, performs provider activation where required, and then drives the same local entitlement path.

`webhook` is the one deliberately public marketplace route. `middleware.ts` exempts only the exact `/api/marketplace/{aws|azure|gcp}/webhook` shape from the human session gate. The handler itself authenticates the provider before any state transition:

- AWS: SNS topic pinning, constrained HTTPS signing-certificate URL, X.509 validity, SignatureVersion 1/2 verification, product/account/license identity preservation;
- Microsoft: signed Entra bearer validation, configured audience/tenant/caller application validation, Fulfillment v2 operation lookup, and success/failure acknowledgement for ChangePlan/ChangeQuantity/Reinstate;
- Google: Pub/Sub OIDC audience/service-account validation, Procurement entitlement lookup, account/product identity preservation, and entitlement/plan-change approve-or-reject after local admission.

Every provider event is claimed in `platform_console.marketplace_events` under `(provider,event_id)`. Exact replays are idempotent, payload-changing replays are `REFUSED:IDEMPOTENCY_KEY_CONFLICT`, and concurrent in-flight duplicates are blocked rather than double-actuated.

## Existing runtime ownership is preserved

Marketplace commerce does not create a second quota or billing-state database. Provider observations converge into the already-owned runtime controls:

```text
provider plan → configured ProjectTier → setProjectTier() → Project label + ResourceQuota
provider lifecycle → PlanState → setPlanState() → active/suspended runtime access
provider quantity → exact durable commercial event fact
```

`plan-state.ts` remains the runtime source of truth for active/past_due/suspended access. `tiers.ts` remains the product-tier/quota source of truth. Marketplace plan and quantity facts are retained independently so commercial semantics are not collapsed into a boolean access flag.

## Receipt-gated usage and billing

`usage` is intentionally separate from entitlement ingress and stays behind owner/API-key authorization. A usage report is refused unless:

1. provider, buyer, agreement, and subscription match a durable marketplace binding;
2. units and time window are valid;
3. `sourceReceipt` is already present in the hash-chained audit store's trusted receipt custody;
4. `(provider,event_id)` is either new or an exact replay of the same usage payload.

Only then does the runtime call the provider metering API:

- AWS Marketplace `BatchMeterUsage` using short-lived runtime credentials and SigV4;
- Microsoft Marketplace metered billing `usageEvent`;
- Google Service Control `check` followed by `report` using the entitlement's usage-reporting identity.

Provider acknowledgements are stored in `platform_console.marketplace_usage_events`; exact retries return the stored acknowledgement instead of double-metering.

## Registration projections

### AWS Marketplace

Registration resolves `CustomerAWSAccountId`, `ProductCode`, and `LicenseArn`, then validates a matching entitlement before a tenant binding can be created. AWS credentials come from runtime environment credentials or the container credential endpoint; the code does not embed provider keys.

### Microsoft Marketplace

Registration resolves the marketplace SaaS token through Fulfillment v2, preserves purchaser/beneficiary tenant and subscription identity, verifies the configured offer, activates the resolved subscription, and binds the exact subscription to the selected internal tenant.

### Google Cloud Marketplace

Registration verifies the signed `x-gcp-marketplace-token` against Google's Cloud Commerce Partner certificate endpoint and the configured partner-domain audience, approves the procurement account, then binds the exact procurement account/product identity. Subsequent entitlement IDs remain distinct, which supports multiple orders for the same account/product without collapsing them into account identity.

## Canonical graph

`ontology/marketplace-commerce.ttl` is the public ontology; `ontology/marketplace-commerce.shacl.ttl` defines structural admission shapes.

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

Every constitutional transition is represented by a BLAKE3-sealed core `Receipt`; operational provider events are additionally persisted in the platform's durable audit/event stores. Provider IDs are projections onto this graph, never replacements for internal identities.

## External blockers that code cannot manufacture

| Requirement | Standing | Promotion evidence |
|---|---|---|
| AWS seller/product enrollment | `UNKNOWN/BLOCKED` | authenticated seller account, accepted product, live test agreement |
| Microsoft seller/offer enrollment | `UNKNOWN/BLOCKED` | authenticated publisher, transactable offer, live resolved subscription |
| Google Cloud vendor/product enrollment | `UNKNOWN/BLOCKED` | vendor account, approved product, live procurement account/entitlement |
| Tax profile | `BLOCKED` | provider-accepted legal tax profile |
| Payout profile | `BLOCKED` | provider-accepted payout destination |
| Fortune-5 contractual SLA | `BLOCKED` | executed customer agreement/SLA with remedies |
| SOC 2 attestation | `BLOCKED` | independent auditor opinion |
| Production HA/DR | `BLOCKED` | executed multi-AZ/multi-region failure and recovery receipts |
| Live metering/settlement | `BLOCKED` | provider-accepted meter and settlement tied to the exact receipt DAG |

No fixture, ontology triple, CI result, source file, synthetic payload, or generated adapter may promote those external facts to `ALIVE`.

## Verification

`.github/workflows/marketplace-commerce.yml` verifies the exact candidate SHA, Rust formatting/clippy/tests, three-provider commerce fixtures, JSON schema syntax, and the complete platform-console TypeScript graph with `npm ci && npx tsc --noEmit`.

`scripts/crown.sh` executes the Rust marketplace fixture verifier before Crown admission evidence is manufactured.

Promotion to live `MARKETPLACE_ALIVE` still requires a real buyer fixture for every admitted provider:

```text
purchase
→ provider identity resolution
→ tenant binding
→ entitlement
→ provider ACK
→ fulfillment
→ artifact / DO receipt
→ receipt-gated usage
→ provider meter acceptance
→ billing/settlement observation
→ reconciliation
→ cancellation/revocation refusal
→ replay
```

Seller enrollment, legal/tax authority, customer risk acceptance, spend authority, contract approval, and production release remain separate authority classes.
