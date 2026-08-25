from .portfolio import Portfolio

def dominates(a: Portfolio, b: Portfolio) -> bool:
    va=(a.interval.lower, -a.interval.width, a.breakdown_gamma, -a.cost, -a.latency)
    vb=(b.interval.lower, -b.interval.width, b.breakdown_gamma, -b.cost, -b.latency)
    return all(x>=y for x,y in zip(va,vb)) and any(x>y for x,y in zip(va,vb))

def frontier(items: tuple[Portfolio,...]) -> tuple[Portfolio,...]:
    return tuple(sorted((x for x in items if not any(dominates(y,x) for y in items if y is not x)), key=lambda p:p.digests))
