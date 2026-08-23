# Replicated Evidence State — Reference

**Diátaxis role:** Reference. This is the authoritative operational documentation for `scripts/develop_train/replicated_evidence_state` at repository baseline `be27c93621ef494ccc342e0dc36c99dab9e391a6` and descendants that do not change the package contract.

## Scope and standing

The package is a deterministic, in-memory qualification capsule for multiple replica observations of one exact subject. Its positive result is `PARTIAL_ALIVE`; it does not manufacture repository-wide `ALIVE` and it performs no consequential actuation.

The package was exact-head exercised on PR #133 head `7ce703f477eeb135f675156d71644a33ac532c1d` by workflow `DEVELOP Replicated Evidence Exact Head`, run `32608335688`, conclusion `success`. The merged default-branch subject is `be27c93621ef494ccc342e0dc36c99dab9e391a6`.

## Public package exports

`scripts.develop_train.replicated_evidence_state` exports:

- `ReplicatedEvidenceEngine`
- `Qualification`
- `Refused`

Supporting types are imported from their modules: `ActionClass`, `Lease`, `ReplicaState`, `VectorClock`, `Mutation`, `Receipt`, `Subject`, and `replay`.

## Qualification contract

`ReplicatedEvidenceEngine.qualify(states, lease, now, action=ActionClass.CONSTRUCT) -> Qualification`

Order of admission:

1. `admit_action(action)` refuses consequential `DO`.
2. `states` is materialized as a list.
3. the lease must admit `now`.
4. replica subjects must agree and the highest generation must not split brain.
5. one `(subject, generation, value_digest)` tuple must hold a strict majority.
6. current winning replica digests are Merkle-reduced.
7. a `Receipt(..., standing="PARTIAL_ALIVE", actuation_performed=False)` is returned.

Results:

| Condition | Result |
|---|---|
| valid lease + consistent strict-majority winner | `Qualification("PARTIAL_ALIVE", receipt)` |
| split brain at highest generation | `Qualification("UNKNOWN", None)` |
| no strict majority | `Qualification("UNKNOWN", None)` |
| invalid/stale/inadmissible input | typed `Refused` |
| `ActionClass.DO` | `REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]` |

## Quorum

`quorum_size(n) = n // 2 + 1` for `n >= 1`. Empty input is refused. Qualification groups replicas by exact `(subject, generation, value_digest)` and requires the largest group to meet this threshold.

## Lease

`Lease(not_before, expires_at)` requires timezone-aware bounds and `not_before < expires_at`. Admission is half-open: `not_before <= now < expires_at`. A naive `now` is refused; an otherwise valid but expired/not-yet-valid lease causes the engine to refuse `STALE_REPLICA_LEASE`.

## Conflict semantics

`classify(states)` refuses an empty set or mixed subjects. It examines only the maximum generation. More than one value digest at that generation is `SPLIT_BRAIN`; otherwise it is `CONSISTENT`.

## Vector clocks

`VectorClock.from_dict` rejects empty clocks, empty replica names, or negative counters. `compare` returns exactly `EQUAL`, `BEFORE`, `AFTER`, or `CONCURRENT`. `increment` advances one replica. `join` takes the component-wise maximum and refuses an empty join.

## Mutation monotonicity

`Mutation` requires `to_generation == from_generation + 1` and a 64-character value digest; violations are typed refusals.

## Merkle and receipts

`merkle_root` sorts hexadecimal digests before reduction, duplicates the final node for odd-width levels, hashes with SHA-256, and refuses an empty set. `Receipt.body()` uses schema `chatman.develop-replicated-evidence-state/1`. `Receipt.digest()` hashes canonical compact, key-sorted JSON with SHA-256.

`replay(receipt, expected_digest)` is true only when no actuation was performed and the receipt digest equals the expected digest.

## Refusal codes

Observed source codes: `BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO`, `EMPTY_REPLICA_SET`, `MIXED_SUBJECTS`, `STALE_REPLICA_LEASE`, `INVALID_LEASE`, `NAIVE_TIME`, `EMPTY_MERKLE_SET`, `NON_MONOTONE_GENERATION`, `INVALID_VALUE_DIGEST`, `INVALID_REPLICA_STATE`, `INEXACT_SUBJECT`, `INVALID_VECTOR_CLOCK`, and `EMPTY_CLOCK_JOIN`.

## Unsupported / excluded behavior

This capsule does not implement a consensus protocol, network transport, remote replication, leader election, cloud/service mutation, or BRCE actuation. Its exact-head workflow explicitly rejects ambient imports of common HTTP, cloud SDK, socket, and subprocess actuation surfaces. Those exclusions are part of the capability boundary, not missing proof of hidden behavior.
