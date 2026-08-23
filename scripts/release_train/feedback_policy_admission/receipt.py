from dataclasses import dataclass
import hashlib,json
from .errors import Refused
SCHEMA="chatman.realized-feedback-admission/1"
@dataclass(frozen=True)
class Receipt:
    body: dict
    digest: str
def manufacture(body):
    payload=dict(body)
    if payload.get("actuation_performed") is not False: raise Refused("ACTUATION_REPORTED")
    raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    return Receipt(payload,hashlib.sha256(raw).hexdigest())
def replay(receipt):
    expected=manufacture(receipt.body)
    if expected.digest != receipt.digest: raise Refused("RECEIPT_MISMATCH")
    return True
