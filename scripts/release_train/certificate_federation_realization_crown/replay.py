from dataclasses import asdict
from hashlib import sha256
import json
from .receipt import Receipt
from .refusal import Refused

def replay(receipt: Receipt) -> str:
    body=asdict(receipt); digest=body.pop("digest")
    if body["authority"] != "SELECT" or body["actuation_performed"]:
        raise Refused("RECEIPT_AUTHORITY_DRIFT")
    expected=sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    if expected != digest: raise Refused("RECEIPT_TAMPER")
    return "REPLAY_MATCH"
