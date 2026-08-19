# 39. Distributors, Resellers, and Channel Partners

## Commerce becomes a multi-party graph

A channel transaction can contain ISV, marketplace operator, distributor, reseller, systems integrator, managed service provider, referral partner, and end customer. Each party can have different authority, margin, support responsibility, and contractual relationship.

```text
Transaction = Graph(Actors, Roles, Authority, Money, Rights, Evidence)
```

A two-party `seller_id`/`buyer_id` schema cannot represent this faithfully.

## Role is not authority

Being named `reseller` does not automatically authorize every commercial action. The graph should encode which party may quote, publish private offers, transact, receive margin, provision, support, amend, renew, or terminate.

Authority can also be marketplace-specific. A partner authorized to participate in an AWS channel private offer has not automatically gained authority in Microsoft or direct sales.

## End-customer entitlement remains visible

The economically transacting intermediary and the product consumer may differ. Entitling the reseller instead of the end customer can produce the wrong tenant, support identity, data boundary, and renewal state.

Model both:

```text
CommercialIntermediary
EndCustomerOrganization
EndCustomerTenant
```

with explicit agreement and delegation edges.

## Money flow

Marketplace fee, distributor margin, reseller margin, referral fee, service revenue, and ISV payout are distinct financial edges. Reconciliation should preserve them rather than reporting only net cash.

```text
Customer charge
  → marketplace fee
  → channel allocation
  → seller payout
```

The exact flow depends on the program; canonical finance objects describe roles without assuming one vendor formula.

## Support responsibility

A reseller or MSP may provide L1 support while the ISV owns L2/L3. A systems integrator may own deployment while the seller owns SaaS runtime. Those responsibilities should be part of the offer/agreement projection and support receipt.

## Attribution

Referral and co-sell attribution should be recorded independently from entitlement. Losing attribution is a revenue-operations defect; granting runtime rights from an opportunity record is an authority defect.

## Refusals

- `REFUSED:CHANNEL_ROLE_AS_AMBIENT_AUTHORITY`
- `REFUSED:RESELLER_ENTITLED_INSTEAD_OF_END_CUSTOMER`
- `REFUSED:CHANNEL_MARGIN_AS_MARKETPLACE_FEE`
- `REFUSED:ONE_MARKET_PARTNER_AUTHORITY_TRANSFERRED_TO_ANOTHER`
- `REFUSED:PIPELINE_ATTRIBUTION_AS_RUNTIME_RIGHT`

## Operational exercise

Model ISV + marketplace + distributor/reseller + Fortune 5 buyer. Draw agreement, offer, authority, entitlement, fulfillment, support, charge, fee, margin, payout, and evidence edges. Then remove the reseller and prove the canonical product/entitlement model does not need to change.
