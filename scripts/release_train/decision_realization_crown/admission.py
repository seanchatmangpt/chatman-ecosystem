from .errors import Refused
def admit(policy, observations):
    obs=tuple(observations)
    if not obs: raise Refused("EMPTY_REALIZATION_SET")
    seen=set()
    for o in obs:
        if o.obs_id in seen: raise Refused("DUPLICATE_OBSERVATION")
        seen.add(o.obs_id)
        if o.policy_generation != policy.generation: raise Refused("FOREIGN_POLICY_GENERATION")
    return obs
