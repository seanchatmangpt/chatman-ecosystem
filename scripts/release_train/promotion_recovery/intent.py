import hashlib, json
from dataclasses import dataclass
from .subject import Subject, Refusal
from .lease import IntentLease

@dataclass(frozen=True)
class PromotionIntent:
    consumer: Subject
    cut_id: str
    policy_digest: str
    frontier_digest: str
    nonce: str
    lease: IntentLease
    def __post_init__(self):
        if not self.cut_id or len(self.policy_digest)!=64 or len(self.frontier_digest)!=64 or not self.nonce:
            raise Refusal('REFUSED[INVALID_PROMOTION_INTENT]')
    @property
    def intent_id(self):
        body={'consumer':self.consumer.identity,'cut_id':self.cut_id,'policy':self.policy_digest,'frontier':self.frontier_digest,'nonce':self.nonce,'issued':self.lease.issued_at.isoformat(),'expires':self.lease.expires_at.isoformat()}
        return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
