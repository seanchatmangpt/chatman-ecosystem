from .refusal import Refused

def exact_quorum(component_id, observations, witnesses=(), minimum=2):
    rows=[r for r in observations if r.component_id==component_id and r.status=="RESOLVED"]
    if any(r.relation=="DIVERGED" for r in rows):
        raise Refused("REFUSED[DIVERGED_REF_IN_QUORUM]")
    exact=[r for r in rows if r.relation=="EXACT"]
    names={r.transport.name for r in exact}
    if len(names) < minimum:
        return "INSUFFICIENT"
    pairs={(min(w.left,w.right),max(w.left,w.right)) for w in witnesses if w.admit()}
    if minimum >= 2:
        ordered=sorted(names)
        connected={ordered[0]}
        changed=True
        while changed:
            changed=False
            for a,b in pairs:
                if a in connected and b in names and b not in connected:
                    connected.add(b); changed=True
                if b in connected and a in names and a not in connected:
                    connected.add(a); changed=True
        if len(connected) < minimum:
            raise Refused("REFUSED[UNPROVEN_QUORUM_INDEPENDENCE]")
    return "QUORUM_EXACT"
