from .errors import Refused

def classify(states) -> str:
    states=list(states)
    if not states: raise Refused("EMPTY_REPLICA_SET")
    subjects={s.subject for s in states}
    if len(subjects)!=1: raise Refused("MIXED_SUBJECTS")
    max_generation=max(s.generation for s in states)
    current=[s for s in states if s.generation==max_generation]
    values={s.value_digest for s in current}
    if len(values)>1: return "SPLIT_BRAIN"
    return "CONSISTENT"
