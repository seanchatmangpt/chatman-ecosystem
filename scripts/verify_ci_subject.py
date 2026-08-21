#!/usr/bin/env python3
"""Fail-closed exact-subject verifier for GitHub Actions execution.

GitHub pull_request workflows normally check out a synthetic merge commit. This
verifier binds a CI observation to the pull request head SHA carried by the event,
or to GITHUB_SHA for non-PR events, and emits a replayable receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "chatman.ci-exact-subject/1"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class SubjectError(RuntimeError):
    """Typed exact-subject refusal."""


def require_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA_RE.fullmatch(value.lower()):
        raise SubjectError(f"REFUSED[INVALID_{label.upper()}]")
    return value.lower()


def expected_sha(event_name: str, event: Mapping[str, Any], fallback_sha: str | None) -> tuple[str, str]:
    if event_name == "pull_request":
        pr = event.get("pull_request")
        if not isinstance(pr, Mapping):
            raise SubjectError("REFUSED[MISSING_PULL_REQUEST]")
        head = pr.get("head")
        if not isinstance(head, Mapping):
            raise SubjectError("REFUSED[MISSING_PULL_REQUEST_HEAD]")
        return require_sha(head.get("sha"), "pull_request_head_sha"), "pull_request.head.sha"
    if fallback_sha is None:
        raise SubjectError("REFUSED[MISSING_FALLBACK_SHA]")
    return require_sha(fallback_sha, "fallback_sha"), "github.sha"


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def build_receipt(*, event_name: str, event: Mapping[str, Any], fallback_sha: str | None, actual_sha: str) -> dict[str, Any]:
    expected, expected_source = expected_sha(event_name, event, fallback_sha)
    actual = require_sha(actual_sha, "actual_sha")
    if actual != expected:
        raise SubjectError(f"REFUSED[SUBJECT_SHA_MISMATCH] expected={expected} actual={actual}")
    observation = {
        "schema": SCHEMA,
        "event_name": event_name,
        "expected_sha": expected,
        "expected_source": expected_source,
        "actual_sha": actual,
        "standing": "VERIFIED",
        "claim": "checked-out commit equals admitted CI subject",
    }
    digest = hashlib.sha256(canonical_bytes(observation)).hexdigest()
    return {
        **observation,
        "receipt": {
            "algorithm": "sha256",
            "observation_digest": digest,
            "replay": "recompute canonical JSON without receipt and require exact digest equality",
        },
    }


def verify_receipt(payload: Mapping[str, Any]) -> bool:
    receipt = payload.get("receipt")
    if not isinstance(receipt, Mapping):
        return False
    expected = receipt.get("observation_digest")
    if not isinstance(expected, str):
        return False
    observation = dict(payload)
    observation.pop("receipt", None)
    actual = hashlib.sha256(canonical_bytes(observation)).hexdigest()
    if actual != expected:
        return False
    return observation.get("expected_sha") == observation.get("actual_sha") and observation.get("standing") == "VERIFIED"


def git_head() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], check=True, text=True, capture_output=True)
    return proc.stdout.strip()


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-name")
    parser.add_argument("--event-path", type=Path)
    parser.add_argument("--fallback-sha")
    parser.add_argument("--actual-sha")
    parser.add_argument("--output", type=Path, default=Path(".artifacts/activity-census/subject.json"))
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args(argv)

    if args.replay:
        payload = json.loads(args.replay.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping) or not verify_receipt(payload):
            print("REFUSED[CI_SUBJECT_RECEIPT_REPLAY]", file=sys.stderr)
            return 2
        print(payload["actual_sha"])
        return 0

    if not args.event_name or args.event_path is None:
        parser.error("--event-name and --event-path are required unless --replay is used")
    try:
        event = json.loads(args.event_path.read_text(encoding="utf-8"))
        if not isinstance(event, Mapping):
            raise SubjectError("REFUSED[INVALID_EVENT_PAYLOAD]")
        receipt = build_receipt(
            event_name=args.event_name,
            event=event,
            fallback_sha=args.fallback_sha,
            actual_sha=args.actual_sha or git_head(),
        )
    except (OSError, json.JSONDecodeError, SubjectError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    write_json(args.output, receipt)
    print(receipt["actual_sha"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
