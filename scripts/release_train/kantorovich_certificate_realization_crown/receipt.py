import hashlib,json
from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class Receipt:
    body: dict
    digest: str
    @classmethod
    def make(cls, body):
        b=dict(body); b['actuation_performed']=False
        raw=json.dumps(b,sort_keys=True,separators=(',',':')).encode()
        return cls(b,hashlib.sha256(raw).hexdigest())
def replay(r):
    raw=json.dumps(r.body,sort_keys=True,separators=(',',':')).encode()
    if r.body.get('actuation_performed') is not False: raise Refused('REPORTED_ACTUATION')
    if hashlib.sha256(raw).hexdigest()!=r.digest: raise Refused('RECEIPT_TAMPER')
    return 'REPLAY_MATCH'
