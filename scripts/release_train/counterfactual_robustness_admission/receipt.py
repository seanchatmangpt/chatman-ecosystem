from dataclasses import dataclass
import hashlib,json
from .refusal import refuse

def canonical(body): return json.dumps(body,sort_keys=True,separators=(',',':')).encode()
@dataclass(frozen=True)
class Receipt:
    body: dict
    digest: str
def manufacture(body):
    if body.get('actuation_performed') is not False: refuse("ACTUATION_REPORTED")
    return Receipt(body,hashlib.sha256(canonical(body)).hexdigest())
def replay(r):
    if r.body.get('actuation_performed') is not False: refuse("ACTUATION_REPORTED")
    return hashlib.sha256(canonical(r.body)).hexdigest()==r.digest
