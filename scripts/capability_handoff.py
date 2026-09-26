from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


class HandoffRefused(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def qualify(row: dict[str, Any]) -> dict[str, Any]:
    producer = row.get("producer_subject", "")
    consumer = row.get("consumer_subject", "")
    evidence = row.get("evidence_digest", "")
    capability = row.get("capability", "")
    consequence = row.get("consequence", "")
    standing = row.get("producer_standing", "")

    if not SHA.fullmatch(producer) or not SHA.fullmatch(consumer):
        raise HandoffRefused("SUBJECT_NOT_EXACT")
    if not DIGEST.fullmatch(evidence):
        raise HandoffRefused("EVIDENCE_NOT_CONTENT_ADDRESSED")
    if standing not in {"ALIVE", "PARTIAL_ALIVE"}:
        raise HandoffRefused("PRODUCER_NOT_ADMITTED")
    if not capability or not consequence:
        raise HandoffRefused("SEMANTIC_IDENTITY_MISSING")

    subject = {
        "producer_subject": producer,
        "consumer_subject": consumer,
        "capability": capability,
        "consequence": consequence,
        "evidence_digest": evidence,
    }
    body = {
        "schema": "chatman.capability-handoff-receipt/1",
        "standing": "ADMITTED",
        "subject_digest": digest(subject),
        **subject,
    }
    return {**body, "receipt_digest": digest(body)}


def replay(row: dict[str, Any], receipt: dict[str, Any]) -> bool:
    return qualify(row) == receipt
