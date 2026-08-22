from .subject import Refused

def relation(left, right, edges=()):
    if left.evidence_id==right.evidence_id:
        return "SAME_EVIDENCE"
    if left.source.fingerprints() & right.source.fingerprints():
        return "CORRELATED"
    pair={left.evidence_id,right.evidence_id}
    explicit=[e for e in edges if {e.left_id,e.right_id}==pair]
    if any(e.relation in {"DERIVED_FROM","SHARES_RUN","SHARES_ARTIFACT"} for e in explicit):
        return "CORRELATED"
    if any(e.relation=="INDEPENDENT_ATTESTATION" for e in explicit):
        return "INDEPENDENT"
    return "UNKNOWN"

def assert_independent(left, right, edges=()):
    state=relation(left,right,edges)
    if state!="INDEPENDENT":
        raise Refused(f"REFUSED[UNPROVEN_INDEPENDENCE:{state}]")
    return state
