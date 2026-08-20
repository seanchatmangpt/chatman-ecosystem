# HDITC DfCM Runtime

## Status

This document binds the HDITC book to executable code. The implementation lives in
`crates/hditc` and is intentionally smaller than the book: the book explores the
mathematical language; the crate implements the constitutional transitions that can
be falsified by execution.

HDITC here is **not** a claim that high dimensionality or cognitive opacity creates
cryptographic hardness. Cryptographic identity is provided by ordinary BLAKE3
content binding. The HDITC contribution is the composition of identity, admitted
observation, authority, bounded consequence, receipt reservation, reconciliation,
and replay.

## Executable correspondence

| Book concept | Executable object |
|---|---|
| `O` | `World` before validation |
| `O*` | `World::validate` plus candidate knowledge closure |
| DfCM | `dfcm_frontier` |
| reversible construction | `Candidate::project` |
| authority | `AuthorityGrant` |
| admission | `PreparedDo::prepare` |
| BRCE PREPARE | `ReceiptReservation` |
| exclusive DO | `BrceExecutor::execute` |
| actuator acknowledgement | `ActuationSignal` |
| OBSERVE | `Actuator::observe` |
| RECONCILE | expected + authority-bound checks in `BrceExecutor` |
| DONE | `DoOutcome::Done` only after acknowledgement and observed closure |
| receipt | `DoReceipt` |
| replay | `replay` |
| standing | `DoOutcome::standing` |

## DfCM law

`dfcm_frontier` preserves every candidate that is simultaneously:

1. bound to the same exact subject as the observed world;
2. explicitly marked reversible;
3. based only on required dimensions that are not `critical_unknown`;
4. consistent with the observed pre-state;
5. inside its construction constraints.

Rejected candidates remain in `excluded` with a typed `RefusalCode`; a failed edge
does not collapse the graph. The lawful frontier is sorted deterministically by
option preservation, expected information gain, lower cost, and stable candidate id.

This makes SELECT non-actuating. `Candidate::project` manufactures a counterfactual
state in memory and has no adapter, connector, network, filesystem, or subprocess
authority.

## Admission law

`PreparedDo::prepare` is the only conversion from a reversible candidate into an
actuation carrier. It refuses when:

- exact subjects differ;
- relevant critical dimensions are UNKNOWN;
- the candidate has no idempotency key;
- the authority class is not an exact match;
- the authority grant digest has drifted;
- the candidate's projected consequence exceeds the authority bound;
- no postcondition is supplied;
- the projected world does not satisfy the claimed postcondition.

The prepared carrier binds the candidate digest, authority-grant digest,
pre-actuation world digest, postcondition digest, and idempotency key into a
`ReceiptReservation`.

## Zero unreceipted actuation

`BrceExecutor::execute` has a fixed ordering:

```text
PreparedDo::verify
  -> ReceiptJournal::reserve
  -> Actuator::actuate
  -> Actuator::observe
  -> reconcile exact subject + postconditions + authority bound
  -> DoReceipt::seal
  -> ReceiptJournal::finalize
```

The actuator is never called when reservation persistence fails. This is asserted by
an executable negative test that counts actuator invocations.

If final receipt persistence fails after an actuation attempt, the runtime returns
`BLOCKED:FINALIZE_AFTER_ACTUATION` with the already-durable reservation id. That
reservation is the recovery handle. The runtime does not blind-retry the actuation.

## ACTUATED != DONE

An acknowledged actuator result is necessary but insufficient for DONE.

`DoOutcome::Done` requires all of the following in the same execution:

- a sealed and durably persisted pre-actuation reservation;
- an `ActuationSignal::Acknowledged`;
- a successful post-actuation observation;
- the same exact subject;
- no relevant critical UNKNOWN dimensions;
- every expected postcondition observed;
- every admitted authority consequence bound observed;
- a sealed final `DoReceipt`.

An acknowledged actuation followed by the wrong observed world is `BLOCKED`, not
`ALIVE`.

An ambiguous actuation is `AMBIGUOUS` even if a subsequent snapshot happens to look
like the expected state, because the execution lacks causal acknowledgement. It is
not retried automatically.

## No human fallback edge

The runtime has no `AwaitHuman`, approval callback, escalation callback, or
human-oracle state. Missing knowledge is a typed refusal. Ambiguous actuation is a
bounded terminal outcome for that attempt. Recovery consists of observation,
reconciliation, and replay against the durable reservation/receipt graph—not asking
a human to convert uncertainty into authority.

This does not mean organizations cannot choose policies that grant authority through
human actions. It means a human response is not a hidden runtime transition required
for the DO algorithm to complete.

## Replay law

`replay(receipt, observed)` accepts only a receipt and an observation. It has no
actuator argument and therefore cannot actuate by construction.

Replay verifies:

- receipt integrity;
- DONE standing on the original execution;
- exact subject identity;
- exact observed-world digest;
- postcondition closure;
- authority-bound closure;
- relevant-known closure.

A fresh observation that differs from the receipted observation revokes replay
standing instead of silently transferring ALIVE to a new world.

## Executed falsifiers

The crate contains tests for these negative propositions:

- an irreversible candidate with a better numerical score cannot enter the DfCM
  frontier;
- relevant critical UNKNOWN blocks admission;
- nearby authority (`Draft`) cannot substitute for
  `ModifyExternalObject`;
- failed receipt reservation causes exactly zero actuator calls;
- actuator acknowledgement with a mismatched post-state is not DONE;
- ambiguous actuation is called exactly once and is not promoted;
- replay refuses a different observed world.

These tests are intended to remain permanent guards. Deleting or weakening them to
obtain a green build would violate the repository constitution.

## Verification

The targeted workflow `.github/workflows/hditc-dfcm.yml` executes:

```bash
cargo fmt --package hditc -- --check
cargo test -p hditc --all-targets --locked
cargo clippy -p hditc --all-targets --locked -- -D warnings
```

The first branch execution runs `cargo metadata` to extend the existing lockfile
without updating unrelated dependency versions. If this changes `Cargo.lock`, the
branch-push workflow commits only that lockfile projection and pushes it to the same
branch. The subsequent exact-head run must pass the locked path before the
implementation can claim exact-head ALIVE standing.

## Standing boundary

Passing the crate tests proves the bounded in-process DfCM/BRCE semantics implemented
here. It does **not** prove that an arbitrary cloud, GitHub, payment, infrastructure,
or physical-world adapter is ALIVE. Each real adapter still requires exact-subject
execution, authority, consequence observation, receipt durability, and replay
evidence at its own boundary.
