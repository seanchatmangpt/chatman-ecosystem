from dataclasses import dataclass

@dataclass(frozen=True)
class StoreCandidate:
    kind:str
    transactional:bool
    replayable:bool=True

def candidates():
    return (StoreCandidate("MEMORY",False),StoreCandidate("JSONL",False),StoreCandidate("SQLITE",True))

def select(*, transactional_required=False):
    opts=candidates()
    if not transactional_required: return opts[0]
    return next(o for o in opts if o.transactional)
