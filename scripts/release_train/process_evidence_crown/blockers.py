from itertools import combinations

def minimal_blocker_cutsets(requirements: dict[str,set[str]], failed:set[str]):
    blocked={r: deps & failed for r,deps in requirements.items() if deps & failed}
    universe=sorted(failed)
    cuts=[]
    for k in range(1,len(universe)+1):
        for combo in combinations(universe,k):
            s=set(combo)
            if all(s & deps for deps in blocked.values()) and not any(set(c)<=s for c in cuts): cuts.append(combo)
        if cuts: break
    return tuple(cuts)
