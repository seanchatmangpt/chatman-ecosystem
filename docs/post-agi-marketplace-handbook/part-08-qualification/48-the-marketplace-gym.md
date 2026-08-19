# 48. The Marketplace Gym

## A gym is an executable commercial environment

Marketplace integrations fail in state-space corners that documentation examples rarely exercise: duplicate callbacks, delayed cancellation, ambiguous metering, plan changes during outages, expired credentials, partial fulfillment, channel involvement, and contradictory clocks.

A marketplace gym makes those behaviors executable before real customer rights or money are touched.

```text
Episode =
  World
  × Roles
  × Policies
  × InformationPartitions
  × Authority
```

The gym is a model of a marketplace contract. It is not the marketplace itself.

## World

The world contains products, sellers, buyers, offers, agreements, entitlements, usage, clocks, event queues, vendor API behavior, settlement projections, and failure injectors. The world version binds the public vendor contracts used to construct it.

## Roles are not agents and not authority

Seller, buyer, marketplace operator, channel partner, runtime operator, finance observer, support operator, and adversary are roles in the episode. A planner can control a role, but the role does not gain authority merely because a policy can emit an action.

## Observation and action space

Observations include marketplace callbacks, API state, agreement state, entitlement state, fulfillment health, usage, meter acknowledgments, settlement, and support events.

Actions include purchase, activate, upgrade, suspend, reinstate, renew, cancel, emit usage, submit meter, reject request, expire credentials, delay event, duplicate event, and inject outage.

For a local gym, external-money and production-market writes are excluded by construction.

## Information partitions matter

Do not give every actor perfect state. In reality:

- the seller can receive a callback before a dashboard updates;
- finance can see a settlement file after runtime events;
- the buyer can experience outage while entitlement remains ACTIVE;
- a reseller can know offer status without seeing product telemetry.

Partitions expose assumptions hidden by omniscient mocks.

## Gym receipts

Every episode records seed, world/contract version, starting graph, policy identities, actions, observations, invariants, refusals, final normalized state, and counterexamples. Re-running the same capsule should reproduce the trace unless nondeterminism is explicitly part of the experiment.

## What gym standing means

A successful gym episode can make a simulation capability ALIVE against that exact world. It cannot make the real vendor integration ALIVE. The promotion boundary remains live exact-subject execution.

## Refusals

- `REFUSED:GYM_AS_PRODUCTION_VENDOR`
- `REFUSED:ROLE_AS_AUTHORITY`
- `REFUSED:OMNISCIENT_MOCK_AS_REAL_INFORMATION_TOPOLOGY`
- `REFUSED:SIMULATED_REVIEW_QUEUE_AS_VENDOR_APPROVAL`
- `REFUSED:SYNTHETIC_SUCCESS_AS_LIVE_STANDING`

## Operational exercise

Build an episode that purchases, activates, fulfills, emits usage, upgrades, suspends, reinstates, renews, cancels, terminates, and reconciles. Inject duplicate and delayed events. Require the gym to output a receipt DAG and the exact live experiment still required.
