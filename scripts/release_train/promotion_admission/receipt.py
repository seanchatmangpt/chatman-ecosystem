from __future__ import annotations
import hashlib, json

class ReceiptRefusal(ValueError):
    pass

def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def manufacture_receipt(body: dict) -> dict:
    if body.get("actuation_performed") is not False:
        raise ReceiptRefusal("REFUSED[ACTUATION_BIT_NOT_FALSE]")
    payload={"schema":"chatman.promotion-admission/1","body":body}
    payload["digest_sha256"]=hashlib.sha256(canonical_bytes(payload)).hexdigest()
    return payload

def replay_receipt(receipt: dict) -> bool:
    observed=receipt.get("digest_sha256")
    payload={k:v for k,v in receipt.items() if k!="digest_sha256"}
    expected=hashlib.sha256(canonical_bytes(payload)).hexdigest()
    if observed != expected:
        raise ReceiptRefusal("REFUSED[RECEIPT_MISMATCH]")
    if payload.get("body",{}).get("actuation_performed") is not False:
        raise ReceiptRefusal("REFUSED[ACTUATION_BIT_NOT_FALSE]")
    return True
