# 49. Simulating the Commercial Lifecycle

## Test traces, not endpoints

Marketplace SDK samples typically prove one endpoint in isolation. The product risk lies in the trace connecting many endpoints and systems over time.

The minimum commercial lifecycle is:

```text
Offer
→ Agreement
→ Entitlement
→ Fulfillment
→ Usage
→ Metering
→ Settlement
→ Renewal/Amendment/Termination
```

Simulation should exercise the full trace under both ordinary and adversarial schedules.

## Baseline episode

Seed an admitted product, plan, seller, buyer, and marketplace projection. Execute:

1. discover/select the product;
2. create or select the offer;
3. accept/purchase;
4. resolve the buyer to canonical organization;
5. activate entitlement;
6. fulfill the selected deployment class;
7. observe customer-visible readiness;
8. emit real-shaped usage;
9. freeze and submit meter batches;
10. reconcile billing/settlement projection;
11. renew, change plan, or terminate;
12. verify final entitlement and data lifecycle.

The expected result is not “all HTTP calls returned 200.” It is a canonical final state plus receipts for every consequential edge.

## Adversarial schedule

Re-run with:

- duplicate purchase notification;
- plan-change event delivered after cancellation;
- vendor outage during activation;
- fulfillment failure after some resources exist;
- meter response lost after possible acceptance;
- renewal effective before the seller observes it;
- settlement record missing one batch;
- customer deprovision request during legal retention.

The same effective event set should converge when the vendor semantics permit. If event ordering is genuinely ambiguous, the correct result is typed `UNKNOWN` or manual-authority escalation.

## Effective time versus observed time

Simulation should maintain both clocks. A plan can change at midnight under an agreement even if the callback arrives minutes later. Usage at 00:00:05 must price under the effective plan, not under whichever event the seller saw first.

## Termination is a family of transitions

Commercial rights can terminate before data deletion. Fulfillment resources can be retained for export or grace period. Settlement can continue after service stops. Support can remain active for a migration window. Model these separately.

## Determinism

A fixed seed and contract version should reproduce the same outcome. Random fault generation is valuable only when the seed is recorded and counterexamples can become permanent fixtures.

## Refusals

- `REFUSED:HAPPY_PATH_ONLY_LIFECYCLE`
- `REFUSED:ARRIVAL_TIME_AS_EFFECTIVE_TIME`
- `REFUSED:CANCEL_AS_DELETE_ALL`
- `REFUSED:AMBIGUOUS_RESULT_AS_RETRY`
- `REFUSED:UNREPLAYABLE_RANDOM_COUNTEREXAMPLE`

## Operational exercise

Run the complete lifecycle twice: first in ideal order, then with duplicate/delayed events and an ambiguous meter response. Normalize both traces into canonical state and explain every permitted difference. Any unexplained rights or money difference is a failed qualification.
