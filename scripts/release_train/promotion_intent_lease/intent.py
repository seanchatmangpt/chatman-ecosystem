from dataclasses import dataclass
import hashlib
import json
from .subject import Subject, Refusal
from .cut import CutIdentity
from .strategy import StrategyBinding

@dataclass(frozen=True)
class PromotionIntent:
    consumer: Subject
    cut: CutIdentity
    strategy: StrategyBinding
    policy_digest: str
    nonce: str

    def __post_init__(self):
        if len(self.policy_digest)!=64 or any(c not in '0123456789abcdef' for c in self.policy_digest):
            raise Refusal('REFUSED[INVALID_POLICY_DIGEST]')
        if not self.nonce:
            raise Refusal('REFUSED[EMPTY_INTENT_NONCE]')

    def identity(self) -> str:
        payload={'consumer':str(self.consumer),'cut_id':self.cut.cut_id,'generation':self.cut.generation,
                 'producers':[str(x) for x in self.cut.producers],'strategy':self.strategy.fingerprint(),
                 'policy_digest':self.policy_digest,'nonce':self.nonce}
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
