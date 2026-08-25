from dataclasses import dataclass
from .subject import Subject
from .refusal import Refused

@dataclass(frozen=True)
class Stage:
    name: str
    subject: Subject
    digest: str

REQUIRED=("semantic","reactor","certificate","federation","realization","receipt")

def require_reactor_chain(stages: list[Stage], subject: Subject) -> tuple[str,...]:
    names=tuple(s.name for s in stages)
    if names != REQUIRED: raise Refused("REACTOR_CHAIN_ORDER_MISMATCH")
    if any(s.subject != subject for s in stages): raise Refused("REACTOR_CHAIN_SUBJECT_DRIFT")
    if any(len(s.digest)!=64 for s in stages): raise Refused("REACTOR_CHAIN_DIGEST_INVALID")
    return names
