# Qualify Replicated Evidence — How-to

**Diátaxis role:** How-to Guide. Use this when operating or diagnosing the in-memory replicated-evidence qualifier. Exact API/refusal semantics live in [Reference](../reference/replicated-evidence-state.md).

## Qualify a candidate set

1. Bind every `ReplicaState.subject` to the same exact `owner/repo@40hex` identity.
2. Use timezone-aware datetimes and a lease for which `not_before <= now < expires_at`.
3. Supply the complete bounded replica set to `ReplicatedEvidenceEngine.qualify`.
4. Treat the returned standing literally.

```python
q = ReplicatedEvidenceEngine().qualify(states, lease, now)
if q.standing == "PARTIAL_ALIVE":
    receipt = q.receipt
else:
    assert q.standing == "UNKNOWN"
    assert q.receipt is None
```

## Diagnose `UNKNOWN`

`UNKNOWN` is a non-admission result, not an error to smooth over.

- Same highest generation with different value digests is `SPLIT_BRAIN` and returns `UNKNOWN` with no receipt.
- A candidate without a strict majority quorum returns `UNKNOWN` with no receipt.
- Do not promote either case to `PARTIAL_ALIVE` or `ALIVE` in calling code or documentation.

## Handle typed refusals

Catch `Refused` and branch on `exc.code`; do not parse human prose.

```python
from scripts.develop_train.replicated_evidence_state.errors import Refused

try:
    q = ReplicatedEvidenceEngine().qualify(states, lease, now)
except Refused as exc:
    print(exc.code)
```

Important refusal codes include `STALE_REPLICA_LEASE`, `INVALID_LEASE`, `NAIVE_TIME`, `EMPTY_REPLICA_SET`, `MIXED_SUBJECTS`, `INVALID_REPLICA_STATE`, `INVALID_VECTOR_CLOCK`, `EMPTY_CLOCK_JOIN`, `NON_MONOTONE_GENERATION`, `INVALID_VALUE_DIGEST`, `EMPTY_MERKLE_SET`, and `BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO`.

## Keep consequential DO outside this engine

The default action is `CONSTRUCT`. Passing `ActionClass.DO` is refused before qualification:

```python
from scripts.develop_train.replicated_evidence_state.authority import ActionClass

try:
    ReplicatedEvidenceEngine().qualify(states, lease, now, ActionClass.DO)
except Refused as exc:
    assert exc.code == "BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO"
```

Route consequential mutation through BRCE instead. Do not add network, subprocess, cloud SDK, or HTTP actuation imports to this capsule merely to make a workflow convenient.

## Verify after a change

Run the permanent falsifier court used by the exact-head workflow:

```bash
python -m compileall -q scripts/develop_train/replicated_evidence_state tests/develop_train/replicated_evidence_state
PYTHONPATH=. python -m unittest discover -s tests/develop_train/replicated_evidence_state -p 'test_*.py' -v
```

Then confirm the action-capable import fence remains empty for `requests`, `httpx`, `boto3`, `azure`, `google.cloud`, `socket`, and `subprocess`.
