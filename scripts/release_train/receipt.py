from __future__ import annotations
import hashlib, json
from typing import Any

class ReceiptRefusal(ValueError):
    pass

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def manufacture(payload: dict[str, Any]) -> dict[str, Any]:
    body=dict(payload)
    body.pop("receipt",None)
    digest=hashlib.sha256(canonical_bytes(body)).hexdigest()
    return {**body,"receipt":{"schema":"chatman.release-train/1","sha256":digest,"actuation_performed":False}}

def replay(document: dict[str, Any]) -> bool:
    receipt=document.get("receipt")
    if not isinstance(receipt,dict) or receipt.get("schema")!="chatman.release-train/1":
        raise ReceiptRefusal("REFUSED[RECEIPT_SCHEMA]")
    if receipt.get("actuation_performed") is not False:
        raise ReceiptRefusal("REFUSED[RECEIPT_AUTHORITY_DRIFT]")
    body=dict(document); body.pop("receipt",None)
    expected=hashlib.sha256(canonical_bytes(body)).hexdigest()
    if receipt.get("sha256")!=expected:
        raise ReceiptRefusal("REFUSED[RECEIPT_MISMATCH]")
    return True
