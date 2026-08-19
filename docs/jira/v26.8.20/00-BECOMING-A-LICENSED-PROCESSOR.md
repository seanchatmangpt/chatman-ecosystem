# Becoming a Licensed Payment Processor — Backward-Chain Plan

> **Provenance record.** Written backward from the stated premise — "we do not need Stripe" —
> chained back to what real, currently-missing regulatory, capital, and banking artifacts would
> have to exist for that premise to be true. Same method as
> [`docs/jira/v26.8.19/00-OVERVIEW.md`](../v26.8.19/00-OVERVIEW.md). Unlike that ticket set,
> almost none of this is closable by engineering work — this document says so plainly rather
> than dressing regulatory/capital requirements up as sprint items.
>
> **What this document does not do.** It does not contain, and platform-console will not gain
> from this document, any code that stores, transmits, or processes raw cardholder data (PAN,
> CVV, full track data). Writing that code without the certification chain below already in
> place would create a real security and legal liability for the business this session is
> working on behalf of, not a working feature. This is a boundary this document treats as fixed,
> not a caveat to work around.

## Backward from finished: what "we do not need Stripe" actually requires

For platform-console to process a card transaction without routing through a third-party PCI
DSS Level 1 processor, every one of the following must be real and current simultaneously —
not projected, not "in progress," actually issued and in force:

1. A PCI DSS Level 1 attestation of compliance, from a Qualified Security Assessor, covering
   whatever systems touch cardholder data.
2. Money transmitter licenses (or the equivalent — see the PayFac alternative below) in every
   US state where a paying customer is billed, plus FinCEN MSB registration federally.
3. Either (a) Visa/Mastercard Principal Membership with a sponsoring/settlement bank
   relationship, or (b) a sponsorship arrangement with an existing acquirer/BIN sponsor.
4. A live AML/KYC compliance program: transaction monitoring, suspicious-activity reporting,
   OFAC screening, merchant underwriting if platform-console itself sponsors sub-merchants.
5. Settlement banking relationships and real-time reserve/chargeback-liability capital.

## Real state today

None of the above exists. `app/lib/stripe-billing.ts` is the entire payment surface; every dollar
platform-console has ever moved has gone through Stripe as the PCI-compliant, licensed party.
No PCI assessment has been performed on this codebase (nor should one be attempted — cardholder
data has never touched it, which is the entire reason its own compliance burden is low today,
per the researched sources below).

## Cost and timeline, cited from real current sources (searched 2026-08-19)

### Path A — Direct Visa/Mastercard Principal Membership (full disintermediation)

- **Capital requirement:** €10-50M, per card-scheme principal-membership guidance
  ([demire.eu](https://www.demire.eu/news/120/370/Comprehensive-Guidance-on-Obtaining-Visa-Mastercard-Principal-Membership/),
  [synhedge.com](https://synhedge.com/card-scheme-memberships/)).
- **Timeline:** 18-36 months for full principal membership with direct acquiring capability;
  the scheme application review itself is 6-12 months on top of the licensing prerequisites
  below ([synhedge.com](https://synhedge.com/card-scheme-memberships/)).
- **Prerequisite:** an active regulatory license (EMI, credit institution, or Payment
  Institution) is required *before* a scheme membership application is even eligible
  ([demire.eu](https://www.demire.eu/news/120/370/Comprehensive-Guidance-on-Obtaining-Visa-Mastercard-Principal-Membership/)).

### Path B — 50-state US money transmitter licensing (required regardless of card-network path, if settling US customer funds directly)

- **Cost:** $250K-$435K+ in fixed licensing costs across all 50 states; total startup cost
  including legal, surety bonds, compliance, and technology can exceed $1M
  ([brico.ai](https://www.brico.ai/post/how-much-do-mtls-cost)). Annual maintenance across all
  50 states starts around $225K and rises with transaction volume due to bond requirements
  ([brico.ai](https://www.brico.ai/post/how-much-do-mtls-cost)).
- **Timeline:** 2-4 years for a full 50-state program; New York, California, and a handful of
  others individually run 12-24 months; a phased rollout (not all 50 at once) is the realistic
  approach ([brico.ai](https://www.brico.ai/post/how-much-do-mtls-cost)).
- **Note:** Montana requires no MTL — the only $0-cost state
  ([brico.ai](https://www.brico.ai/post/how-much-do-mtls-cost)).

### Path C — PCI DSS Level 1 certification (required for either path above if touching card data)

- **Cost:** $50K-$200K annually for a Level-1-scale organization to establish and maintain
  compliance; a Level 1 merchant processing 6M+ transactions/year may spend $200K-$500K+
  ([sprinto.com](https://sprinto.com/blog/pci-dss-certification-cost/)).
- **Timeline:** 6-12 months for a full QSA assessment
  ([sprinto.com](https://sprinto.com/blog/pci-dss-certification-cost/)).
- **The counterfactual, stated plainly:** outsourcing to a PCI DSS Level 1 certified processor
  (Stripe, Adyen, etc.) removes the cardholder-data environment from platform-console's own
  systems entirely, which is *why* this compliance burden doesn't exist on this codebase today
  ([sprinto.com](https://sprinto.com/blog/pci-dss-certification-cost/)).

### Path D — Payment Facilitator (PayFac) model — the realistic middle path

- **What it is:** rather than becoming a card-network principal member, a PayFac is sponsored
  into the networks by an existing acquiring bank, gets its own sub-merchant onboarding
  capability, and settles through the sponsor rather than directly with the schemes
  ([Stripe's own PayFac guide](https://stripe.com/guides/payfacs),
  [infinicept.com](https://infinicept.com/payment-facilitator/learn/get-started/what-is-the-relationship-between-payment-facilitators-and-merchant-acquirers/)).
- **Why it's the real answer most "build our own processor" efforts land on:** capital
  requirements are materially lower than Principal Membership (no €10-50M scheme-capital
  requirement), because the sponsor bank still bears settlement/network risk
  ([edgardunn.com](https://www.edgardunn.com/articles/enabling-payment-facilitators-payfacs-business-as-usual-or-a-differentiator-for-acquirers)).
  Still requires PCI DSS Level 1 (Path C above) and still requires state-by-state MTL coverage
  or an equivalent exemption in most cases — a PayFac is not exempt from Path B, only from
  Path A's scheme-capital requirement
  ([usio.com](https://usio.com/how-to-get-pci-level-1-certified/)).
- **What it does not remove:** underwriting risk, chargeback liability, and full AML/KYC
  compliance ownership for every sub-merchant onboarded — the PayFac, not the sponsor bank,
  owns this in the standard model
  ([infinicept.com](https://infinicept.com/payment-facilitator/learn/get-started/what-is-the-relationship-between-payment-facilitators-and-merchant-acquirers/)).

## Backward-chained recommendation, stated as a recommendation, not a directive

Given the real numbers above, chained backward from "process a Fortune 5 customer's card
payment without Stripe":

1. **Path A (direct scheme membership) is disproportionate** for platform-console's actual
   scale — €10-50M capital and 18-36 months to reach a state that a PayFac arrangement reaches
   for a fraction of the capital and, per the researched timelines, plausibly faster.
2. **Path C (PCI DSS Level 1) is required under every real path** that touches cardholder data
   directly — there is no route to "not needing Stripe" that skips this.
3. **Path D (PayFac, sponsored) is the realistic target** if the actual goal is "our own
   branded payment flow, our own economics on interchange" rather than literal
   card-network-principal independence. It still requires Path B (state MTLs, or a documented
   exemption analysis) and Path C (PCI DSS L1) — it removes only Path A's scheme-capital and
   direct-membership-timeline burden.
4. **None of Paths A-D are shortened by anything this session builds in code.** ggen-marketplace
   generation, gymact actuation, or any swarm round in this session's history compresses
   scaffolding and boilerplate, not bank due diligence, state regulator review queues, or a
   QSA's audit calendar — the same distinction this session already drew explicitly in
   [`docs/jira/v26.8.19/05-GYMACT-AUTOFDE-ACTUATION-SCOPE.md`](../v26.8.19/05-GYMACT-AUTOFDE-ACTUATION-SCOPE.md)
   for cloud marketplace review queues applies here with even less give — a bank's underwriting
   committee and a state banking regulator move on their own clock, period.

## What is honestly buildable in this codebase today, if the goal is architectural readiness

Not raw card handling — a real **payment-provider abstraction layer**, so that whichever path
above is eventually chosen (staying on Stripe, adding a second PCI-compliant processor,
eventually sponsoring into a PayFac arrangement), platform-console's billing logic isn't
rewritten from scratch to adopt it:

- Extract `app/lib/stripe-billing.ts`'s public surface behind a real
  `PaymentProvider` interface (`createCustomer`, `createSubscription`, `changeSubscriptionPlan`,
  `applyBalanceCredit`, `listInvoices`, `handleWebhookEvent`) with Stripe as the only real
  implementation today.
- Route `app/lib/plan-state.ts`'s existing `applyEntitlementEvent(source, event)` entrypoint
  (shipped this session, round 12) so a future second provider's webhook is a new `source`
  value, not a parallel state machine — this is already the right shape for exactly this need.
- This is a real, scoped engineering task (days, not the multi-year paths above) and is the
  honest version of "reduce Stripe dependency" available right now — distinct from, and not a
  substitute for, becoming a licensed processor.

This item is offered as a follow-up, not started in this pass — flagging it as the concrete,
buildable alternative to the literal ask, consistent with the first `AskUserQuestion` option
this session presented before writing this document.
