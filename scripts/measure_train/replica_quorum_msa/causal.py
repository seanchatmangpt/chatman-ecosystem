from collections import Counter
def causal_profile(observations):
    relations=Counter(); obs=tuple(sorted(observations))
    for i,a in enumerate(obs):
        for b in obs[i+1:]: relations[a.clock.compare(b.clock)]+=1
    return dict(sorted(relations.items()))
def maximal_observations(observations):
    obs=tuple(sorted(observations)); maximal=[]
    for x in obs:
        if not any(x.clock.compare(y.clock)=="BEFORE" for y in obs if y is not x): maximal.append(x)
    return tuple(maximal)
def concurrency_ratio(observations):
    profile=causal_profile(observations); total=sum(profile.values())
    return 0.0 if total==0 else profile.get("CONCURRENT",0)/total
