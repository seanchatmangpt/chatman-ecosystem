from collections import defaultdict
from .subject import Refused
def classify_quorum(universe,observations):
    by_replica={}
    for o in observations:
        if o.replica_id in by_replica: raise Refused("REFUSED[DUPLICATE_REPLICA_OBSERVATION]")
        by_replica[o.replica_id]=o
    if not set(by_replica)<=set(universe.members): raise Refused("REFUSED[FOREIGN_REPLICA]")
    if len(by_replica)<universe.quorum_size(): return {"state":"INSUFFICIENT","generation":None,"digest":None,"replicas":()}
    groups=defaultdict(list)
    for o in by_replica.values(): groups[(o.generation,o.value_digest)].append(o)
    winners=[(k,v) for k,v in groups.items() if len(v)>=universe.quorum_size()]
    if len(winners)!=1:return {"state":"AMBIGUOUS","generation":None,"digest":None,"replicas":()}
    (generation,digest), rows=winners[0]
    if any(a.clock.compare(b.clock)=="CONCURRENT" and a.value_digest!=b.value_digest for a in rows for b in by_replica.values()):
        return {"state":"CONCURRENT","generation":generation,"digest":digest,"replicas":tuple(sorted(o.replica_id for o in rows))}
    return {"state":"CURRENT_CANDIDATE","generation":generation,"digest":digest,"replicas":tuple(sorted(o.replica_id for o in rows))}
