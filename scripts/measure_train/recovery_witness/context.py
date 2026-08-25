import hashlib, json
from dataclasses import dataclass
from .subject import Subject, Refused

@dataclass(frozen=True, order=True)
class RecoveryContext:
    subject: Subject
    cut_id: str
    policy_digest: str
    frontier_digest: str
    generation: int
    def __post_init__(self):
        if not self.cut_id.strip(): raise Refused("REFUSED[EMPTY_CUT_ID]")
        for value, name in ((self.policy_digest,"POLICY"),(self.frontier_digest,"FRONTIER")):
            if len(value)!=64 or any(c not in "0123456789abcdef" for c in value):
                raise Refused(f"REFUSED[INVALID_{name}_DIGEST]")
        if self.generation < 0: raise Refused("REFUSED[INVALID_GENERATION]")
    @property
    def digest(self):
        raw=json.dumps({"repo":self.subject.repo,"sha":self.subject.sha,"cut":self.cut_id,
                        "policy":self.policy_digest,"frontier":self.frontier_digest,
                        "generation":self.generation},sort_keys=True,separators=(",",":"))
        return hashlib.sha256(raw.encode()).hexdigest()
