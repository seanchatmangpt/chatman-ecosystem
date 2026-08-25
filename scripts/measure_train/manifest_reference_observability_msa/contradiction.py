from .refusal import Refused

def detect(observations):
    grouped={}
    for row in observations:
        if row.status=="RESOLVED":
            grouped.setdefault(row.component_id,set()).add(row.relation)
    contradictions=[]
    for component_id, relations in sorted(grouped.items()):
        if "DIVERGED" in relations and ("EXACT" in relations or "ADVANCED" in relations):
            contradictions.append(component_id)
    return tuple(contradictions)

def require_consistent(observations):
    contradictions=detect(observations)
    if contradictions:
        raise Refused("REFUSED[CROSS_TRANSPORT_REF_CONTRADICTION]:" + ",".join(contradictions))
    return True
