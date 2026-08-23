def temporal_violations(observations):
    by_replica={}; violations=[]
    for o in sorted(observations,key=lambda x:(x.replica_id,x.observed_at)):
        prev=by_replica.get(o.replica_id)
        if prev:
            if o.generation<prev.generation: violations.append((o.replica_id,"GENERATION_REGRESSION"))
            if o.generation==prev.generation and o.value_digest!=prev.value_digest: violations.append((o.replica_id,"SAME_GENERATION_DIVERGENCE"))
            if prev.clock.compare(o.clock)=="AFTER": violations.append((o.replica_id,"CAUSAL_REGRESSION"))
        by_replica[o.replica_id]=o
    return tuple(violations)
