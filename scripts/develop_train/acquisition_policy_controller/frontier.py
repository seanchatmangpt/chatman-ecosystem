from dataclasses import dataclass
from hashlib import sha256
import json
from .subject import Refusal
@dataclass(frozen=True, slots=True)
class PolicyFrontier:
    generation:int
    policy_digest:str
    evidence_digest:str
    @property
    def digest(self): return sha256(json.dumps({"generation":self.generation,"policy_digest":self.policy_digest,"evidence_digest":self.evidence_digest},sort_keys=True,separators=(",",":")).encode()).hexdigest()
def admit_frontier(frontier,policy,current_generation):
    if frontier.generation!=policy.generation or frontier.policy_digest!=policy.digest or current_generation!=policy.generation: raise Refusal("REFUSED_STALE_POLICY_FRONTIER")
    return frontier
