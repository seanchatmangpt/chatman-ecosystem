from .errors import Refused

def quorum_size(n: int) -> int:
    if n < 1: raise Refused("EMPTY_REPLICA_SET")
    return n // 2 + 1

def qualified(states) -> tuple[bool, str | None]:
    states=list(states)
    if not states: raise Refused("EMPTY_REPLICA_SET")
    by_digest={}
    for s in states: by_digest.setdefault((s.subject,s.generation,s.value_digest), []).append(s)
    winner=max(by_digest.items(), key=lambda kv:(len(kv[1]), kv[0]))
    if len(winner[1]) < quorum_size(len(states)): return False, None
    return True, winner[0][2]
