#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "chatman.release-ci-subject/1"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class SubjectRefusal(ValueError):
    pass


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _require_sha(value: str, field: str) -> str:
    normalized = value.strip().lower()
    if not SHA_RE.fullmatch(normalized):
        raise SubjectRefusal(f"REFUSED[SUBJECT_SHA_INVALID] {field}={value!r}")
    return normalized


def manufacture(expected_sha: str, actual_sha: str, event_name: str, source: str) -> dict[str, Any]:
    expected = _require_sha(expected_sha, "expected_sha")
    actual = _require_sha(actual_sha, "actual_sha")
    if expected != actual:
        raise SubjectRefusal(
            f"REFUSED[SUBJECT_SHA_MISMATCH] expected={expected} actual={actual}"
        )
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "event_name": event_name,
        "expected_sha": expected,
        "actual_sha": actual,
        "subject_source": source,
        "standing": "VERIFIED",
        "claim": "EXACT_RELEASE_CI_SUBJECT",
    }
    return {**body, "sha256": hashlib.sha256(_canonical(body)).hexdigest()}


def replay(receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt.get("schema") != SCHEMA:
        raise SubjectRefusal("REFUSED[SUBJECT_RECEIPT_SCHEMA]")
    digest = receipt.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise SubjectRefusal("REFUSED[SUBJECT_RECEIPT_DIGEST_INVALID]")
    body = {key: value for key, value in receipt.items() if key != "sha256"}
    expected_digest = hashlib.sha256(_canonical(body)).hexdigest()
    if digest != expected_digest:
        raise SubjectRefusal("REFUSED[SUBJECT_RECEIPT_TAMPERED]")
    expected = _require_sha(str(receipt.get("expected_sha", "")), "expected_sha")
    actual = _require_sha(str(receipt.get("actual_sha", "")), "actual_sha")
    if expected != actual or receipt.get("standing") != "VERIFIED":
        raise SubjectRefusal("REFUSED[SUBJECT_RECEIPT_NOT_VERIFIED]")
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Exact-subject admission for release CI")
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("manufacture")
    make.add_argument("--expected", required=True)
    make.add_argument("--actual", required=True)
    make.add_argument("--event", required=True)
    make.add_argument("--source", required=True)
    make.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("replay")
    check.add_argument("--receipt", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "manufacture":
            receipt = manufacture(args.expected, args.actual, args.event, args.source)
            args.output.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")
        else:
            receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
            replay(receipt)
    except (OSError, json.JSONDecodeError, SubjectRefusal) as exc:
        print(str(exc))
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
