# Replicated Evidence State — Tutorial

**Diátaxis role:** Tutorial. Follow this path to see one successful, bounded qualification. For the factual contract, use [Reference](../reference/replicated-evidence-state.md).

The replicated-evidence engine combines multiple in-memory replica observations for one exact subject. It does **not** replicate over a network and it does **not** actuate external systems.

## Goal

Produce a `PARTIAL_ALIVE` qualification and deterministic receipt from a strict majority of matching replicas under a valid lease.

## 1. Build one exact subject and three replica states

```python
from datetime import datetime, timedelta, timezone

from scripts.develop_train.replicated_evidence_state.engine import ReplicatedEvidenceEngine
from scripts.develop_train.replicated_evidence_state.lease import Lease
from scripts.develop_train.replicated_evidence_state.replica_state import ReplicaState
from scripts.develop_train.replicated_evidence_state.vector_clock import VectorClock

subject = "seanchatmangpt/chatman-ecosystem@" + "a" * 40
value = "b" * 64
now = datetime.now(timezone.utc)
lease = Lease(now - timedelta(seconds=1), now + timedelta(minutes=5))

states = [
    ReplicaState("r1", subject, 7, value, VectorClock.from_dict({"r1": 7})),
    ReplicaState("r2", subject, 7, value, VectorClock.from_dict({"r2": 7})),
    ReplicaState("r3", subject, 6, "c" * 64, VectorClock.from_dict({"r3": 6})),
]
```

Two of three replicas agree on generation 7 and the same value digest. That is a strict majority.

## 2. Qualify

```python
qualification = ReplicatedEvidenceEngine().qualify(states, lease, now)
assert qualification.standing == "PARTIAL_ALIVE"
assert qualification.receipt is not None
assert qualification.receipt.generation == 7
assert qualification.receipt.value_digest == value
assert qualification.receipt.actuation_performed is False
```

The positive result deliberately stops at `PARTIAL_ALIVE`. This local capsule proves deterministic qualification behavior, not the repository-wide Crown.

## 3. Replay the receipt

```python
from scripts.develop_train.replicated_evidence_state.replay import replay

digest = qualification.receipt.digest()
assert replay(qualification.receipt, digest)
```

Replay verifies the canonical receipt digest and also requires `actuation_performed == False`.

## What you proved

You exercised the bounded path `states + lease -> admission -> conflict check -> quorum -> Merkle evidence -> PARTIAL_ALIVE receipt -> replay`. You did not prove network consensus, remote replication, external mutation, leader election, repository-wide `ALIVE`, or consequential `DO` authority.

Next: use the [how-to guide](../how-to/qualify-replicated-evidence.md) for failure diagnosis and the [explanation](../explanation/replicated-evidence-currentness.md) for the standing boundary.
