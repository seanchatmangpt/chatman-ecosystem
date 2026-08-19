# 38. Private Offers

## The enterprise marketplace primitive

Private offers let a seller project an existing product/plan into buyer-scoped terms: negotiated price, quantity, duration, channel participation, support, or legal material. They are powerful precisely because they avoid creating a new public product for every enterprise negotiation.

```text
PrivateOffer = CanonicalPlan + BuyerScopedAdmittedDelta
```

The delta is explicit and versioned. It does not become a hidden code branch.

## Offer construction

A private-offer intent should bind:

```text
canonical product/version
canonical plan/version
marketplace projection
buyer marketplace identity
seller identity
price/quantity/term delta
legal terms digest
support delta
valid-from / valid-until
channel roles if any
```

Constructing this object is reversible. Publishing/pushing it to the buyer is DO.

## Buyer identity is safety-critical

Private offers are intentionally scoped. AWS, Microsoft, Alibaba, Oracle, and channel programs identify buyers differently. A typo or wrong account can expose negotiated pricing or terms to the wrong organization.

The product therefore resolves the vendor buyer identifier to a canonical organization before DO and receipts both identities afterward.

## Acceptance creates agreement state

The seller must not entitle the buyer because a private offer was published. Entitlement begins only from an admitted acceptance/agreement event under the vendor contract.

```text
DRAFT → PUBLISHED → ACCEPTED → AGREEMENT
              ↘ EXPIRED
              ↘ WITHDRAWN
```

Marketplace-specific amendment and renewal rules remain projection semantics.

## Negotiated legal content

A custom EULA, DPA, or attachment must be an approved legal artifact with a digest and scope. A model can draft or compare terms under CONSTRUCT; the publication intent uses only admitted approved text.

## Renewal and expansion

An expansion may increase quantity, add a capability, extend term, or change support. It should become a new accepted commercial state with effective time rather than mutate the historical offer.

## Refusals

- `REFUSED:PRIVATE_OFFER_TO_UNRESOLVED_BUYER`
- `REFUSED:PUBLISHED_OFFER_AS_ENTITLEMENT`
- `REFUSED:GENERATED_LEGAL_TEXT_AS_APPROVED_ATTACHMENT`
- `REFUSED:EXPIRED_OFFER_AS_ACTIONABLE`
- `REFUSED:CUSTOMER_CODE_FORK_INSTEAD_OF_COMMERCIAL_DELTA`

## Operational exercise

Model a three-year Fortune 5 private offer with committed usage, premium support, a negotiated DPA, and a reseller. Show canonical plan invariants, buyer-scoped deltas, marketplace IDs, publication authority, acceptance evidence, entitlement transition, renewal, and exact receipt fields.
