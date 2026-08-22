from dataclasses import dataclass
from hashlib import sha256
import json

SCHEMA="chatman.detector-consensus-recovery/1"
def canonical(payload): return json.dumps(payload,sort_keys=True,separators=(",",":"))

@dataclass(frozen=True)
class Receipt:
    payload:dict
    digest:str

def issue(payload):
    body=dict(payload); body["schema"]=SCHEMA; body["actuation_performed"]=False
    return Receipt(body,sha256(canonical(body).encode()).hexdigest())

def replay(receipt):
    if receipt.payload.get("schema")!=SCHEMA or receipt.payload.get("actuation_performed") is not False:
        raise ValueError("REFUSED[RECEIPT_AUTHORITY_DRIFT]")
    if sha256(canonical(receipt.payload).encode()).hexdigest()!=receipt.digest:
        raise ValueError("REFUSED[RECEIPT_TAMPER]")
    return True
