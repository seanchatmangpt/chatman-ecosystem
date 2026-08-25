from .acquisition import AcquisitionCandidate

def dominates(a:AcquisitionCandidate,b:AcquisitionCandidate)->bool:
    ge=a.information_gain>=b.information_gain and a.independence_gain>=b.independence_gain and a.cost<=b.cost and a.latency<=b.latency
    strict=a.information_gain>b.information_gain or a.independence_gain>b.independence_gain or a.cost<b.cost or a.latency<b.latency
    return ge and strict

def frontier(candidates:list[AcquisitionCandidate])->tuple[str,...]:
    return tuple(sorted(c.candidate_id for c in candidates if not any(dominates(o,c) for o in candidates if o is not c)))
