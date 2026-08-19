# Appendix H — Marketplace Gym Specification

A marketplace gym models commercial behavior without pretending to be the vendor.

## World

```text
World = {
  marketplace_contract_version,
  products,
  buyers,
  offers,
  agreements,
  entitlements,
  clocks,
  event_queues,
  failure_injectors,
  accounting_projection
}
```

## Roles

Typical roles:

```text
seller
buyer
marketplace_operator
channel_partner
runtime_operator
support_operator
finance_observer
adversary
```

A role is not an authority grant.

## Observation space

- marketplace notifications;
- API observations;
- agreement state;
- entitlement state;
- usage observations;
- fulfillment observations;
- settlement statements;
- support events;
- vendor documentation/contract version.

## Action space

Gym actions can include purchase, activate, change plan, suspend, reinstate, cancel, emit usage, reject meter, delay callback, duplicate event, expire credentials, fail deployment, and generate settlement variance.

Real marketplace writes are outside the gym authority boundary.

## Information partitions

Do not give every actor perfect information by default. The seller may see an entitlement notification before a settlement record. The buyer may observe service unavailability while the marketplace still shows ACTIVE. Information partitions expose reconciliation assumptions.

## Episode receipt

Every episode records seed, world version, policy identities, actions, observations, invariants, failures, and final normalized state.

## Graduation

A gym can advance a candidate by falsifying bad designs and proving deterministic behavior within the simulated contract. It cannot promote a live marketplace capability to ALIVE. That requires observed execution against the exact real subject.
