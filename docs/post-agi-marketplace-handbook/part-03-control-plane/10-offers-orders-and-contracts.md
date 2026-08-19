# 10. Offers, Orders, and Contracts

## Proposal is not obligation

Offer, order, agreement, and contract are often rendered on one marketplace page, but they are different commercial objects.

An **offer** proposes a configuration of plan, price, term, quantity, support, and legal terms. An **order** is a buyer action requesting or accepting a purchase. An **agreement** is the durable accepted commercial relationship. A **contract** is the legally operative set of obligations represented by or associated with that agreement.

The distinction matters because rights must derive from accepted state, not from a proposal that can expire or be withdrawn.

## Canonical state

```text
Offer: DRAFT → OFFERED → ACCEPTED | EXPIRED | WITHDRAWN
Agreement: PENDING → ACTIVE → AMENDED* → RENEWED* → TERMINATED
```

Accepted history is immutable. An amendment creates a new effective state or version; it does not rewrite what was agreed last quarter.

## Public and private offers

A public offer is reusable across eligible buyers. A private offer adds buyer-scoped commercial deltas such as negotiated price, term, quantity, channel participation, or approved legal attachments.

```text
PrivateOffer = CanonicalPlan + BuyerScopedAdmittedDelta
```

That equation prevents bespoke enterprise commerce from becoming bespoke source-code forks. If the runtime behavior differs, the difference should be represented as an admitted capability/plan or policy delta.

## Effective time

Commercial systems have at least two clocks: when an event is observed and when terms become effective. Renewals, future-dated agreements, downgrades at term end, and amendments make the difference unavoidable.

Every agreement transition should retain:

```text
observed_at
effective_at
previous_agreement_version
source_offer_or_event
canonical_plan_version
```

## Marketplace differences remain explicit

AWS private-offer amendment rules differ by SaaS pricing model. Microsoft plan/pricing constraints differ from AWS. Alibaba private offers are pushed to a specific customer account identity. Those are projection facts, not reasons to create one vague `PrivateOffer` abstraction that claims more equivalence than exists.

## Authority

Constructing a draft offer is CONSTRUCT. Publishing or sending a buyer-scoped offer is DO. Accepting an agreement is generally an external buyer/marketplace action observed by the seller; the seller does not invent acceptance because a sales representative says the customer intends to buy.

## Refusals

- `REFUSED:OFFER_AS_ENTITLEMENT`
- `REFUSED:EXPIRED_OFFER_ACCEPTANCE`
- `REFUSED:AGREEMENT_HISTORY_REWRITE`
- `REFUSED:UNMAPPED_PRIVATE_TERMS`
- `REFUSED:SALES_FORECAST_AS_CONTRACT`

## Operational exercise

Represent five traces: public purchase, buyer-scoped private offer, amendment, renewal, and cancellation. For each, identify the object that changes, effective time, source authority, entitlement consequence, and receipt. Preserve marketplace-specific amendment limitations as projection rules.
