from __future__ import annotations
from dataclasses import dataclass

class CandidateRefusal(ValueError):
    pass

@dataclass(frozen=True)
class Candidate:
    name: str
    durable: bool
    transactional: bool
    reversible: bool=True

CANDIDATES=(
    Candidate("MEMORY",False,False),
    Candidate("JSONL",True,False),
    Candidate("SQLITE",True,True),
)

def select(*, require_durable: bool, require_transactional: bool) -> Candidate:
    eligible=[c for c in CANDIDATES if c.reversible]
    if require_durable:
        eligible=[c for c in eligible if c.durable]
    if require_transactional:
        eligible=[c for c in eligible if c.transactional]
    if not eligible:
        raise CandidateRefusal("REFUSED[NO_REVERSIBLE_CANDIDATE]")
    return sorted(eligible,key=lambda c:(c.transactional,c.durable,c.name))[0]
