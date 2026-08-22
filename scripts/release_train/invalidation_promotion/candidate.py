from dataclasses import dataclass

@dataclass(frozen=True)
class Candidate:
    name: str
    durable: bool
    transactional: bool
    reversible: bool=True

def candidates():
    return (
      Candidate('memory',False,False), Candidate('jsonl',True,False), Candidate('sqlite',True,True)
    )
def select_candidate(*, require_durable=False, require_transactional=False):
    lawful=[c for c in candidates() if c.reversible and (not require_durable or c.durable) and (not require_transactional or c.transactional)]
    return sorted(lawful,key=lambda c:(not c.transactional,not c.durable,c.name))[0]
