from .errors import Refused
def current(items):
    if not items: raise Refused("NO_CURRENT_CALIBRATION")
    g=max(x.generation for x in items)
    xs=[x for x in items if x.generation==g]
    digests={x.digest for x in xs}
    if len(digests)!=1: raise Refused("DIVERGENT_CURRENT_CALIBRATION")
    return xs[0]
