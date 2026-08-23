from .acquisition import information_gain

def dominates(a,b):
    av=(information_gain(a),a.independence_gain,-float(a.cost),-float(a.latency_seconds))
    bv=(information_gain(b),b.independence_gain,-float(b.cost),-float(b.latency_seconds))
    return all(x>=y for x,y in zip(av,bv)) and any(x>y for x,y in zip(av,bv))

def frontier(candidates):
    candidates=tuple(candidates)
    return tuple(c for c in candidates if not any(dominates(o,c) for o in candidates if o!=c))
