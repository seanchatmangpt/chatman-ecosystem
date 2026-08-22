from __future__ import annotations

import hashlib, json
from dataclasses import dataclass

class Refusal(ValueError):
    pass

def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",",":"), ensure_ascii=True).encode()

@dataclass(frozen=True)
class Receipt:
    schema: str
    body: dict
    digest: str

def manufacture(body: dict) -> Receipt:
    payload=dict(body)
    payload["actuation_performed"]=False
    digest=hashlib.sha256(_canonical(payload)).hexdigest()
    return Receipt("chatman.current-frontier-promotion/1", payload, digest)

def replay(receipt: Receipt) -> None:
    if receipt.schema != "chatman.current-frontier-promotion/1": raise Refusal("REFUSED[RECEIPT_SCHEMA]")
    if receipt.body.get("actuation_performed") is not False: raise Refusal("REFUSED[RECEIPT_AUTHORITY_DRIFT]")
    if hashlib.sha256(_canonical(receipt.body)).hexdigest() != receipt.digest: raise Refusal("REFUSED[RECEIPT_MISMATCH]")
