# Appendix K — Running the Complete Marketplace Laboratory

The laboratory should be cheap, deterministic, and destructive only inside explicit sandboxes.

## Local layer

Run:

```text
ontology validation
schema validation
deterministic ggen projection
adapter unit/property tests
state-machine fixtures
receipt verification
replay
```

No cloud credentials are required for this layer.

## Gym layer

Execute lifecycle episodes for every marketplace projection:

```text
purchase
activate
provision
usage
meter
upgrade
suspend
reinstate
renew
cancel
terminate
reconcile
```

Inject duplicates, delays, credential expiry, vendor outages, provisioning failures, meter rejection, and settlement mismatches.

## Vendor sandbox layer

For each vendor, pin:

```text
seller/test account
buyer/test account
product/listing version
adapter commit
artifact digest
vendor API/version observation
authority scope
cost ceiling
```

Execute the narrowest real operation that proves the target capability.

## Live layer

Live marketplace publication or real-money transactions require explicit authority. The laboratory must not infer this authority from valid credentials or repository ownership.

## Teardown

Teardown is a DO operation. It must have the same discipline as creation:

```text
select exact resources
construct teardown intent
admit authority
delete/cancel
verify postcondition
receipt
```

## Cost controls

Set per-marketplace budgets, resource TTLs, test tenant caps, and metering ceilings. Test infrastructure should default to zero or near-zero idle cost. External seller-review clocks are not accelerated by keeping infrastructure running.

## Result

The lab emits a marketplace capability matrix with exact-subject standing, receipts, replay results, exclusions, and the next falsifier.
