from .subject import Refused
def propagate(nodes, edges, standings):
    deps={n:[] for n in nodes}
    for c,p in edges:
        if c not in deps or p not in deps: raise Refused("REFUSED[UNKNOWN_DEPENDENCY]")
        deps[c].append(p)
    visiting=set(); memo={}
    def calc(n):
        if n in visiting: raise Refused("REFUSED[DEPENDENCY_CYCLE]")
        if n in memo:return memo[n]
        visiting.add(n); inherited=[calc(x) for x in deps[n]]; visiting.remove(n)
        own=standings.get(n,"UNKNOWN")
        if any(v in {"BUILD_BROKEN","BLOCKED"} for v in inherited): own="BLOCKED"
        elif any(v=="UNKNOWN" for v in inherited) and own=="PARTIAL_ALIVE": own="UNKNOWN"
        memo[n]=own; return own
    return {n:calc(n) for n in sorted(nodes)}
