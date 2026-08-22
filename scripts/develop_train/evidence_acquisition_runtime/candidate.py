from dataclasses import dataclass
from fractions import Fraction
import hashlib
from .subject import Refusal
_ALLOWED={'VERIFY','OBSERVE','SELECT','CONSTRUCT'}
@dataclass(frozen=True, slots=True)
class EvidenceCandidate:
    candidate_id:str; family:str; domain:str; scope:str; cost:Fraction; latency_ms:int; authority:str='SELECT'
    def __post_init__(self):
        if not all(x and '\n' not in x for x in (self.candidate_id,self.family,self.domain,self.scope)): raise Refusal('REFUSED_INVALID_EVIDENCE_CANDIDATE')
        if self.cost<0 or self.latency_ms<0: raise Refusal('REFUSED_INVALID_EVIDENCE_COST')
        if self.authority not in _ALLOWED: raise Refusal('REFUSED_BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO')
    @property
    def fingerprint(self):
        raw='\x1f'.join((self.candidate_id,self.family,self.domain,self.scope,str(self.cost),str(self.latency_ms),self.authority))
        return hashlib.sha256(raw.encode()).hexdigest()
