from dataclasses import dataclass, asdict
import hashlib, json
from .refusal import require

@dataclass(frozen=True)
class Receipt:
    schema: str
    subject: str
    generation: int
    standing: str
    evidence_digest: str
    strategy: str
    authority: str='SELECT'
    actuation_performed: bool=False
    digest: str=''

    def body(self) -> dict:
        d=asdict(self); d.pop('digest'); return d

    def seal(self) -> 'Receipt':
        encoded=json.dumps(self.body(),sort_keys=True,separators=(',',':')).encode()
        return Receipt(**self.body(),digest=hashlib.sha256(encoded).hexdigest())

def replay(receipt: Receipt) -> str:
    require(receipt.authority!='DO' and not receipt.actuation_performed,'RECEIPT_ACTUATION_CLAIM')
    require(receipt.seal().digest==receipt.digest,'RECEIPT_TAMPER')
    return 'REPLAY_MATCH'
