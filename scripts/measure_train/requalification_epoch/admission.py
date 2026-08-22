from .subject import Refused

ORDER={"DELIVERY":0,"ACKNOWLEDGEMENT":1,"DISCHARGE":2,"RECOVERY":3}

def admit_witness(epoch, witness, prior=()):
    if witness.producer != epoch.producer: raise Refused("REFUSED[FOREIGN_PRODUCER]")
    if witness.generation < epoch.generation: raise Refused("REFUSED[STALE_INVALIDATION_EPOCH]")
    if witness.generation > epoch.generation: raise Refused("REFUSED[FUTURE_INVALIDATION_EPOCH]")
    if witness.event_id != epoch.event_id: raise Refused("REFUSED[FOREIGN_INVALIDATION_EVENT]")
    if witness.observed_at < epoch.observed_at: raise Refused("REFUSED[WITNESS_PREDATES_EPOCH]")
    same=[p for p in prior if p.consumer==witness.consumer and p.producer==witness.producer and p.generation==witness.generation and p.event_id==witness.event_id]
    if witness.kind != "DELIVERY":
        required=ORDER[witness.kind]-1
        parents=[p for p in same if ORDER[p.kind]==required]
        if not parents or witness.parent_id not in {p.witness_id for p in parents}:
            raise Refused("REFUSED[CAUSAL_WITNESS_GAP]")
        parent=next(p for p in parents if p.witness_id==witness.parent_id)
        if witness.observed_at < parent.observed_at: raise Refused("REFUSED[CAUSAL_TIME_REGRESSION]")
    return "ADMITTED"
