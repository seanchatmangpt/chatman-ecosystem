# 70. Qualify the Marketplace Matrix

## Qualification is an information-gain schedule

After generation, the problem changes from manufacture to falsification. Run the cheapest gates that can kill the largest number of bad candidates before spending time, credentials, vendor review cycles, or customer money.

A useful ladder is:

```text
1. source correspondence
2. ontology / SHACL / schema
3. deterministic regeneration
4. compile / package / lint
5. canonical invariants
6. positive fixtures
7. negative fixtures
8. property / state-machine tests
9. marketplace gym
10. chaos / fault injection
11. differential cross-market tests
12. vendor sandbox/test execution
13. live exact-subject execution
14. receipt + replay
```

Not every capability requires every rung. The required verifier is defined by the standing claim.

## Matrix cell as an evidence object

Each cell should contain more than pass/fail:

```text
marketplace
capability
canonical semantic
vendor semantic / mapping kind
exact source subject
exact generated artifact
verification command or external experiment
result / exit / observed postcondition
receipt
standing
exclusions
next falsifier
```

A marketplace may therefore be ALIVE for container packaging, PARTIAL_ALIVE for SaaS entitlement, BLOCKED on seller review, and UNKNOWN for metering.

## Stop on the first informative defect

When a gate fails:

1. preserve the exact failure;
2. identify the transition it falsifies;
3. construct a new repair hypothesis;
4. repair the narrowest owning surface;
5. encode a permanent negative fixture or constraint;
6. rerun the failed boundary;
7. expand validation only after it passes.

Do not rerun an unchanged failure hoping the environment will become green. Do not weaken acceptance merely because a vendor sample behaves differently from the product invariant.

## Differential qualification

Once two markets pass their local lifecycle tests, run equivalent canonical scenarios through both and compare normalized state at every transition.

This is where hidden plan or lifecycle drift becomes visible. A successful AWS adapter and a successful Microsoft adapter can each be locally correct while still granting different rights to the same canonical plan.

## Sandbox and live are separate subjects

Sandbox/test accounts are invaluable because they exercise real authentication, APIs, and vendor behavior at low consequence. Their receipts prove those exact environments. Production marketplace standing requires separate exact-subject evidence when the claim depends on it.

External seller/certification queues remain `BLOCKED` until the vendor acts.

## CI is transport, not truth

Hosted CI can validate reproducible structural and behavioral gates, but workflow metadata is not execution evidence by itself. The receipt records exact job/run identity and result. Live vendor tests should be isolated behind explicit credentials and authority; ordinary pull-request CI must not gain ambient commercial DO.

## Promotion

Only after the required boundary executes and verifies does a cell advance:

```text
UNKNOWN → PARTIAL_ALIVE → ALIVE
```

`BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, and `REFUSED:*` remain orthogonal typed outcomes rather than percentages of success.

## Refusals

- `REFUSED:CHEAP_GATE_SKIPPED_FOR_LIVE_TEST`
- `REFUSED:UNCHANGED_FAILURE_RERUN`
- `REFUSED:NEGATIVE_FIXTURE_WEAKENED`
- `REFUSED:SANDBOX_EVIDENCE_AS_PRODUCTION_ALIVE`
- `REFUSED:WORKFLOW_EXISTENCE_AS_SUCCESSFUL_RUN`
- `REFUSED:MARKETPLACE_PERCENT_READY_AS_STANDING`

## Operational exercise

Take the generated marketplace matrix from Chapter 69. Run or specify the qualification ladder for every cell, preserving exact identities. Sort remaining non-ALIVE cells by cheapest high-information falsifier rather than vendor prestige. The output is a receipt-backed matrix, not a readiness percentage.
