from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class ReactorCorrespondence:
    semantic_digest:str; reactor_digest:str; projection_digest:str; trace_digest:str; receipt_digest:str; same_subject:bool
    def admit(self):
        if not self.same_subject: raise Refused("REACTOR_SUBJECT_DRIFT")
        if any(len(x)!=64 for x in (self.semantic_digest,self.reactor_digest,self.projection_digest,self.trace_digest,self.receipt_digest)): raise Refused("MALFORMED_REACTOR_CORRESPONDENCE")
        return True
