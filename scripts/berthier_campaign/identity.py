"""Content-addressed identities for Berthier campaign artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_bytes(payload: Any) -> bytes:
    """Return stable JSON bytes suitable for identity and replay boundaries."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def stable_id(kind: str, payload: Any) -> str:
    """Derive a deterministic typed SHA-256 identity from canonical payload bytes."""
    normalized_kind = kind.strip()
    if not normalized_kind:
        raise ValueError("kind must be non-empty")
    return f"{normalized_kind}:sha256:{hashlib.sha256(canonical_bytes(payload)).hexdigest()}"
