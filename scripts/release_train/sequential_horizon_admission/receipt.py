import hashlib,json
from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class Receipt:
    body:dict; digest:str
def make_receipt(body):
    if body.get("actuation_performed") is not False: raise Refused("RECEIPT_MUST_BIND_NO_ACTUATION")
    if body.get("authority")!="SELECT": raise Refused("INVALID_RECEIPT_AUTHORITY")
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return Receipt(body,hashlib.sha256(raw.encode()).hexdigest())
def replay(receipt): return make_receipt(dict(receipt.body)).digest==receipt.digest
