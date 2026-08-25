from .refusal import Refused

def admit_observations(components, observations, now):
    components=tuple(components)
    by_id={c.component_id:c for c in components}
    if len(by_id) != len(components):
        raise Refused("REFUSED[DUPLICATE_COMPONENT]")
    seen={}
    out=[]
    for row in observations:
        if row.component_id not in by_id:
            raise Refused("REFUSED[UNKNOWN_COMPONENT]")
        if row.observed_at > now:
            raise Refused("REFUSED[FUTURE_OBSERVATION]")
        key=(row.component_id,row.transport.name,row.transport.generation,row.evidence_id)
        previous=seen.get(key)
        if previous is not None and previous != row:
            raise Refused("REFUSED[CONTRADICTORY_DUPLICATE_OBSERVATION]")
        seen[key]=row
        out.append(row)
    return tuple(sorted(set(out)))
