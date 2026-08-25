def dominates(a,b):
    av=(a.expected_loss,a.false_precision_risk,a.evidence_cost,-a.information_gain)
    bv=(b.expected_loss,b.false_precision_risk,b.evidence_cost,-b.information_gain)
    return all(x<=y for x,y in zip(av,bv)) and any(x<y for x,y in zip(av,bv))
def frontier(candidates):
    cs=tuple(candidates)
    return tuple(c for c in cs if not any(d is not c and dominates(d,c) for d in cs))
