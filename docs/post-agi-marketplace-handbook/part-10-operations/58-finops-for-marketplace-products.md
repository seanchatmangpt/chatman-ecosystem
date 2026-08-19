# 58. FinOps for Marketplace Products

## Optimize the whole unit, not only cloud spend

Marketplace product economics include runtime COGS, marketplace fees, channel margin, support cost, service credits, payment/settlement effects, data/AI costs, and operational labor. Infrastructure cost is only one term.

```text
GrossMargin =
  NetRevenue
  - RuntimeCOGS
  - MarketplaceFees
  - ChannelCost
  - SupportCost
  - Credits/Refunds
```

The exact accounting treatment remains finance/accounting authority; engineering provides traceable commercial facts.

## Product and tenant attribution

Costs should map to canonical product/version, deployment class, plan, and—where policy allows—tenant/customer. Shared platform cost needs an explicit allocation policy rather than an arbitrary equal split hidden in a dashboard.

Useful dimensions include:

- compute/storage/network;
- AI/model/token inference cost;
- observability/security services;
- private connectivity;
- data transfer;
- support effort;
- marketplace fee;
- channel margin;
- credits and SLA exposure.

## Realized revenue versus list price

List price is not realized revenue. Private-offer discounts, commitments, credits, refunds, marketplace fees, and channel participation can make realized unit economics very different across markets.

The canonical agreement and settlement receipts supply the actual commercial path.

## Price-to-cost drift

A plan that was profitable at launch can degrade as infrastructure, model, support, or vendor fees change. Monitor cost per billable unit and gross margin by plan/marketplace.

This does not authorize autonomous price changes. It constructs evidence for SELECT and approved pricing policy.

## Customer-hosted economics

Customer-hosted deployments may shift compute cost to the customer while increasing support, qualification, upgrade, and enterprise-networking cost. “No cloud bill” is not zero COGS.

## SLA risk

Service credits and high-support tiers are contingent cost. Model expected exposure and observe actual incidents. A plan can have healthy average gross margin while one reliability defect creates concentrated credit/support risk.

## Refusals

- `REFUSED:LIST_PRICE_AS_REALIZED_REVENUE`
- `REFUSED:MARKETPLACE_PAYOUT_AS_GROSS_SALES`
- `REFUSED:SHARED_COST_WITHOUT_ALLOCATION_POLICY`
- `REFUSED:AUTONOMOUS_PRICE_CHANGE_FROM_MARGIN_ALERT`
- `REFUSED:CUSTOMER_HOSTED_AS_ZERO_COGS`

## Operational exercise

Calculate unit economics for vendor-hosted SaaS, customer-hosted Kubernetes, and a channel/private-offer deal. Include marketplace fees, support, private networking, runtime cost, credits, and partner margin. Show which facts come from receipts and which remain accounting policy inputs.
