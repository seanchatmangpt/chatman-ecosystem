from __future__ import annotations
import hashlib, json
from dataclasses import dataclass
from typing import Any

SCHEMA="chatman.ack-discharge-promotion/1"

@dataclass(frozen=True)
class Receipt:
    schema: str
    digest: str
    body: dict[str,Any]

def _canonical(body: dict[str,Any]) -> bytes:
    return json.dumps(body,sort_keys=True,separators=(",",":")).encode()

def manufacture(body: dict[str,Any]) -> Receipt:
    normalized=dict(body)
    normalized["actuation_performed"]=False
    return Receipt(SCHEMA,hashlib.sha256(_canonical(normalized)).hexdigest(),normalized)

def replay(receipt: Receipt) -> bool:
    if receipt.schema != SCHEMA or receipt.body.get("actuation_performed") is not False:
        return False
    return hashlib.sha256(_canonical(receipt.body)).hexdigest()==receipt.digest
