# 15. Billing, Settlement, and Reconciliation

## Three different questions

**Billing** asks what the commercial system says is owed. **Settlement** records what the marketplace or payment rail actually charged, withheld, credited, and paid out. **Reconciliation** proves those records correspond to the agreement and measured product usage.

Collapsing the three produces dashboards that look correct while unexplained money accumulates in the gaps.

```text
MeasuredUsage
   ↕
MeterSubmission ↔ MarketplaceCharge ↔ Fees/Tax/Credits ↔ Payout
   ↕
Agreement/Price                ↕
                     Internal financial record
```

## One right, one billing route

A product can be sold directly and through marketplaces, but one entitlement must not be charged through two rails for the same period. The agreement records the active commercial route. Stripe, AWS, Microsoft, Oracle, or another payment path becomes a projection of that route rather than a parallel source of truth.

`REFUSED:DOUBLE_BILLING_RISK` should be a hard gate, not a finance cleanup task.

## Settlement is not gross revenue

Marketplace settlement can include vendor fees, channel margin, tax handling, refunds, credits, timing differences, currency conversion, and reserves. The system should retain the marketplace's own settlement identity and explain each transformation rather than equating payout cash with product revenue.

Accounting recognition is a separate professional/accounting authority boundary. The engineering system provides exact commercial facts; it does not invent recognition policy.

## Reconciliation as a join over durable identities

A defensible reconciliation record can answer:

- which agreement and plan were effective;
- which usage events formed each meter batch;
- which batch the marketplace accepted or rejected;
- what customer charge or invoice reference resulted;
- what fees, credits, taxes, and adjustments were applied;
- what payout/settlement record followed;
- what remains unmatched and why.

An unexplained residual remains an exception. It is not rounded into success.

## Corrections

Corrections preserve history. If an accepted usage batch was wrong, create the vendor-supported adjustment or corrective transaction and link it to the original receipt. Never rewrite the old batch and destroy the evidence used to charge the buyer.

## SLOs for money paths

Commercial operations need SLOs for meter acceptance, settlement import freshness, reconciliation completeness, and exception age. An API can be 99.99% available while financial standing is degraded because batches have been rejected for days.

## Refusals

- `REFUSED:DUAL_BILLING_SAME_RIGHT`
- `REFUSED:PAYOUT_AS_GROSS_REVENUE`
- `REFUSED:UNEXPLAINED_RECONCILIATION_RESIDUAL`
- `REFUSED:HISTORICAL_BATCH_REWRITE`
- `REFUSED:ENTITLEMENT_AS_ACCOUNTING_JUDGMENT`

## Operational exercise

Trace one monthly customer period from raw usage through meter batch, vendor acceptance, customer charge, marketplace fee, refund/credit if any, payout, and internal reconciliation. Every amount must map to an exact agreement and receipt. Leave unmatched items visibly `PARTIAL_ALIVE` or `UNKNOWN` rather than forcing a closed period.
