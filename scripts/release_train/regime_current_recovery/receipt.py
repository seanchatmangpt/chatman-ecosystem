from dataclasses import dataclass
import hashlib, json
from .subject import Refusal

SCHEMA='chatman.regime-current-recovery/1'
def canonical(value) -> bytes: return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()

@dataclass(frozen=True)
class Receipt:
    body: dict
    digest: str

def manufacture(body: dict) -> Receipt:
    payload=dict(body); payload['schema']=SCHEMA; payload['actuation_performed']=False
    return Receipt(payload,hashlib.sha256(canonical(payload)).hexdigest())

def replay(receipt: Receipt) -> bool:
    if receipt.body.get('schema')!=SCHEMA or receipt.body.get('actuation_performed') is not False: raise Refusal('REFUSED[RECEIPT_AUTHORITY_DRIFT]')
    return hashlib.sha256(canonical(receipt.body)).hexdigest()==receipt.digest
