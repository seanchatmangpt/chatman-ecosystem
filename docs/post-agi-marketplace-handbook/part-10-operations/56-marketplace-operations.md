# 56. Marketplace Operations

## Commercial state needs SRE

A platform can be technically healthy while commerce is broken. New customers may be unable to activate, entitlement changes may lag, meter batches may be rejected, private offers may expire unexpectedly, or settlement may be unreconciled.

Marketplace operations is SRE over the code-to-cash graph.

## Commercial SLIs

Useful indicators include:

```text
purchase-to-entitlement latency
entitlement-to-fulfillment latency
fulfillment success rate
meter batch acceptance rate
meter reporting age
settlement import freshness
reconciliation completion
private-offer failure rate
listing health / publication drift
support response by plan
```

These complement API latency and infrastructure uptime.

## Incident boundary

Every alert should map to a commercial transition and affected subjects. “Marketplace API error rate high” is less actionable than “AWS meter batches for product vX have exceeded reporting-age SLO for 17 active agreements.”

The incident response loop is:

```text
observe
→ identify affected commercial objects
→ preserve failing evidence
→ classify transition
→ construct repair
→ admit authority
→ actuate if required
→ verify
→ reconcile
→ receipt
→ encode guard
```

## Graceful degradation

Marketplace outages should not cause undefined behavior. Examples:

- existing active entitlements can continue under bounded cached policy;
- new plan changes can be BLOCKED until authoritative state returns;
- usage events can queue within vendor reporting limits;
- private-offer publication can stop safely;
- refunds with ambiguous state can stop for manual authority.

The behavior is product/market-specific and should be tested in gyms.

## Operational ownership

Commercial incidents can cross engineering, finance, sales operations, support, partner operations, and legal. Receipts and canonical IDs create the shared language needed to hand work between teams without guessing.

## Vendor deprecation

Marketplace APIs and policies change. Operations should monitor vendor contract/source drift as a reliability signal. A deprecated API can turn a previously ALIVE adapter into a time-bounded risk before any customer incident occurs.

## Refusals

- `REFUSED:HTTP_UPTIME_AS_COMMERCIAL_HEALTH`
- `REFUSED:BILLING_FAILURE_AS_FINANCE_ONLY`
- `REFUSED:ENTITLEMENT_REPAIR_WITHOUT_RECEIPT`
- `REFUSED:MARKETPLACE_DEPRECATION_IGNORED`
- `REFUSED:AMBIGUOUS_FINANCIAL_INCIDENT_AUTORETRY`

## Operational exercise

Define five commercial SLOs that ordinary service uptime cannot substitute for. For each, specify exact subject, metric, threshold/window, owner, alert, repair authority, verifier, and the customer agreements affected by breach.
