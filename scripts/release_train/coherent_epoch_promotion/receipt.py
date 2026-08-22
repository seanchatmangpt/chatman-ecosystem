from __future__ import annotations
from dataclasses import dataclass
import hashlib, json

SCHEMA='chatman.coherent-epoch-promotion/1'

@dataclass(frozen=True)
class Receipt:
    schema: str
    digest: str
    payload: dict
    actuation_performed: bool=False

def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()

def manufacture(payload: dict) -> Receipt:
    bound={'schema':SCHEMA,'payload':payload,'actuation_performed':False}
    digest=hashlib.sha256(_canonical(bound)).hexdigest()
    return Receipt(SCHEMA,digest,payload,False)

def replay(receipt: Receipt) -> bool:
    if receipt.schema != SCHEMA or receipt.actuation_performed:
        return False
    return manufacture(receipt.payload).digest == receipt.digest
