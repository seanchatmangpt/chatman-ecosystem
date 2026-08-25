from .errors import Refused

def admit(policy, observations):
    seen=set()
    out=[]
    for o in observations:
        if o.observation_id in seen:
            raise Refused("DUPLICATE_OBSERVATION")
        seen.add(o.observation_id)
        if o.policy_generation != policy.generation:
            raise Refused("FOREIGN_POLICY_GENERATION")
        out.append(o)
    if not out:
        raise Refused("EMPTY_REALIZATION_SET")
    return tuple(out)
