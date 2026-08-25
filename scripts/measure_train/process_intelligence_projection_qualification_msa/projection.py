from dataclasses import dataclass
from .subject import Subject
from .refusal import Refused
@dataclass(frozen=True, order=True)
class Projection:
    projection_id:str; subject:Subject; methodology:str; engine:str; runtime:str; evidence_root:str; semantic_digest:str; result_digest:str
    def __post_init__(self):
        if not all([self.projection_id,self.engine,self.runtime,self.evidence_root]): raise Refused("REFUSED[EMPTY_PROJECTION_IDENTITY]")
        for d in (self.semantic_digest,self.result_digest):
            if len(d)!=64 or any(c not in "0123456789abcdef" for c in d): raise Refused("REFUSED[INVALID_PROJECTION_DIGEST]")
