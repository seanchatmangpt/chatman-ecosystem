#!/usr/bin/env python3
"""Deterministic cross-repository exact-subject evidence manifest.

Consumes JSON observations and refuses evidence that cannot be bound to one exact
repository subject. This is SELECT/MEASURE only: no actuation or standing promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ALLOWED_RESULTS = {"PASS", "FAIL", "PENDING", "UNKNOWN", "UNSUPPORTED"}

class Refusal(ValueError):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(f"REFUSED[{code}]: {detail}")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _validate_subject(subject: dict[str, Any]) -> tuple[str, str]:
    repo, sha = subject.get("repo"), subject.get("sha")
    if not isinstance(repo, str) or not REPO.fullmatch(repo):
        raise Refusal("INVALID_REPOSITORY", repr(repo))
    if not isinstance(sha, str) or not SHA40.fullmatch(sha):
        raise Refusal("INVALID_SUBJECT_SHA", repr(sha))
    return repo, sha


def _normalize_observation(obs: dict[str, Any], expected_repo: str, expected_sha: str) -> dict[str, Any]:
    if not isinstance(obs, dict):
        raise Refusal("MALFORMED_OBSERVATION", "observation must be object")
    repo = obs.get("repo")
    sha = obs.get("sha")
    if repo != expected_repo or sha != expected_sha:
        raise Refusal("STALE_OR_FOREIGN_SUBJECT", f"expected {expected_repo}@{expected_sha}, got {repo}@{sha}")
    sensor = obs.get("sensor")
    result = obs.get("result")
    evidence_id = obs.get("evidence_id")
    if not isinstance(sensor, str) or not sensor.strip():
        raise Refusal("MISSING_SENSOR", repr(sensor))
    if result not in ALLOWED_RESULTS:
        raise Refusal("INVALID_RESULT", repr(result))
    if not isinstance(evidence_id, str) or not evidence_id.strip():
        raise Refusal("MISSING_EVIDENCE_ID", repr(evidence_id))
    recorded_at = obs.get("recorded_at")
    if recorded_at is not None and not isinstance(recorded_at, str):
        raise Refusal("INVALID_RECORDED_AT", repr(recorded_at))
    return {
        "repo": repo,
        "sha": sha,
        "sensor": sensor.strip(),
        "result": result,
        "evidence_id": evidence_id.strip(),
        "recorded_at": recorded_at,
        "details": obs.get("details", {}),
    }


def manufacture(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise Refusal("MALFORMED_INPUT", "root must be object")
    subject = payload.get("subject")
    if not isinstance(subject, dict):
        raise Refusal("MISSING_SUBJECT", "subject object required")
    repo, sha = _validate_subject(subject)
    raw = payload.get("observations")
    if not isinstance(raw, list):
        raise Refusal("MISSING_OBSERVATIONS", "observations array required")

    normalized = [_normalize_observation(o, repo, sha) for o in raw]
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for obs in normalized:
        key = (obs["sensor"], obs["evidence_id"])
        prior = seen.get(key)
        if prior is not None and digest(prior) != digest(obs):
            raise Refusal("CONFLICTING_DUPLICATE_EVIDENCE", f"sensor={key[0]} evidence_id={key[1]}")
        seen[key] = obs
    unique = sorted(seen.values(), key=lambda o: (o["sensor"], o["evidence_id"], o["result"]))

    counts = {r: sum(1 for o in unique if o["result"] == r) for r in sorted(ALLOWED_RESULTS)}
    if not unique:
        standing = "UNKNOWN"
        reason = "NO_EVIDENCE"
    elif counts["FAIL"]:
        standing = "BUILD_BROKEN"
        reason = "OBSERVED_FAILURE"
    elif counts["PENDING"] or counts["UNKNOWN"]:
        standing = "UNKNOWN"
        reason = "INCOMPLETE_EVIDENCE"
    elif counts["UNSUPPORTED"] and counts["PASS"] == 0:
        standing = "UNSUPPORTED"
        reason = "NO_SUPPORTED_SENSOR"
    else:
        standing = "PARTIAL_ALIVE"
        reason = "MEASUREMENT_EVIDENCE_ONLY"

    body = {
        "schema": "chatman.measure.exact-subject-evidence-manifest/v1",
        "subject": {"repo": repo, "sha": sha},
        "observations": unique,
        "counts": counts,
        "standing": standing,
        "standing_reason": reason,
        "authority": "SELECT_MEASURE_ONLY",
        "claim_ceiling": "PARTIAL_ALIVE",
    }
    return {**body, "receipt": {"algorithm": "sha256", "digest": digest(body)}}


def verify(manifest: dict[str, Any]) -> bool:
    receipt = manifest.get("receipt") if isinstance(manifest, dict) else None
    if not isinstance(receipt, dict) or receipt.get("algorithm") != "sha256":
        raise Refusal("INVALID_RECEIPT", "sha256 receipt required")
    expected = receipt.get("digest")
    if not isinstance(expected, str) or len(expected) != 64:
        raise Refusal("INVALID_RECEIPT", "digest must be 64 hex chars")
    body = {k: v for k, v in manifest.items() if k != "receipt"}
    if digest(body) != expected:
        raise Refusal("RECEIPT_MISMATCH", "manifest content does not match receipt")
    replay = manufacture({"subject": body["subject"], "observations": body["observations"]})
    if replay != manifest:
        raise Refusal("REPLAY_MISMATCH", "deterministic replay differs")
    return True


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("--verify", action="store_true")
    args = p.parse_args()
    data = json.loads(args.input.read_text())
    try:
        out = data if args.verify else manufacture(data)
        if args.verify:
            verify(out)
        print(json.dumps(out, sort_keys=True, indent=2))
        return 0
    except Refusal as exc:
        print(json.dumps({"refusal": exc.code, "detail": exc.detail}, sort_keys=True))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
