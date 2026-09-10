# Appendix U — Cloud Simulation Protocol

Cloud simulation in Chateco is a controlled experiment over an admitted model of a provider surface. It is not a claim that a mock HTTP server, Terraform plan, or API schema is equivalent to AWS, Azure, GCP, Oracle Cloud, or any other live control plane. The protocol exists to make that distinction executable while still extracting high-value evidence before expensive or consequential live tests.

## Subject identity

Every episode binds a provider, service/API version, region or location model, identity/permission model, resource graph, fixture or recorded corpus version, planner/policy identity, and deterministic seed where stochastic behavior exists. A result without those coordinates is not replayable and cannot be compared across runs.

## World construction

The simulated world is assembled from documented request/response schemas, lifecycle state machines, quotas, error classes, dependency relationships, eventual-consistency behavior where modeled, and explicit UNKNOWN dimensions where fidelity is absent. Unsupported behavior must remain `UNSUPPORTED` rather than being filled with a convenient success response.

## Action boundary

Actions are modeled as typed intents such as create, read, update, delete, attach, detach, deploy, or reconcile. The simulation may project their consequences into its world state, but it carries no production credential and does not manufacture real cloud authority. A policy that succeeds only because the simulator grants impossible permissions is a benchmark defect.

## Observation and reward

The observation projection determines what the policy is allowed to know. Reward should measure objective closure—correct resource state, bounded cost, safety, reversibility, or recovery—not merely API call count or absence of exceptions. Hidden provider state may be used by the verifier but must not leak into the policy unless the real interface exposes it.

## Fidelity ladder

1. **Schema fidelity** — request/response and validation behavior.
2. **Lifecycle fidelity** — legal state transitions and dependency ordering.
3. **Failure fidelity** — authorization, quota, conflict, timeout, and partial-failure classes.
4. **Temporal fidelity** — delays, retries, eventual consistency, and long-running operations.
5. **Cross-resource fidelity** — side effects across dependent resources.
6. **Live differential fidelity** — bounded comparison against authorized real API executions.

A simulator may be ALIVE at one rung while remaining PARTIAL_ALIVE for the next. Fidelity is never implied by the word “exact.”

## Differential verification

For operations authorized for live testing, the same normalized intent is executed in simulation and against an isolated live subject. Observations are reduced to a declared comparison projection so volatile provider metadata does not create false mismatches. Every unexplained difference becomes a model defect or an explicit fidelity exclusion.

## Failure and replay

Timeout after possible actuation, asynchronous operation completion, quota exhaustion, credential expiry, provider-side conflict, and stale read-after-write are first-class scenarios. Replay uses the recorded world, seed, intent sequence, and verifier; it does not replay real cloud mutations. Live retries require a fresh authority/idempotency decision at the real boundary.

## Standing

Simulation evidence can crown the simulator and the policy behavior inside its admitted model. It cannot crown a production deployment, billing path, marketplace entitlement, or destructive cloud operation. Those claims require exact-subject live evidence and their own receipts.
