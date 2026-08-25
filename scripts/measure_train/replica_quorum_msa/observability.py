from fractions import Fraction
import math
def replica_entropy(universe,observations):
    seen={o.replica_id for o in observations}
    if not seen:return 0.0
    p=1/len(seen)
    return -len(seen)*p*math.log2(p)
def observability(universe,observations):
    coverage=universe.coverage(observations)
    return {"coverage":coverage,"quorum_covered":len({o.replica_id for o in observations})>=universe.quorum_size(),"entropy_bits":replica_entropy(universe,observations)}
def monotone_visibility(before,after,universe):
    return observability(universe,after)["coverage"]>=observability(universe,before)["coverage"]
