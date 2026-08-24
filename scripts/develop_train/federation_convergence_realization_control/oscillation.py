from .potential import potential
def recurrent(trajectory):
    seen=set(); previous=None
    for o in trajectory.observations:
        p=potential(o)
        if p == previous: continue
        if p in seen: return True
        seen.add(p); previous=p
    return False
