from .subject import Refused

def dependency_standing(nodes, edges, standings):
    deps={n:[] for n in nodes}
    for a,b in edges:
        if a not in deps or b not in deps: raise Refused("REFUSED[UNKNOWN_DEPENDENCY]")
        deps[a].append(b)
    visiting=set(); memo={}
    def calc(n):
        if n in visiting: raise Refused("REFUSED[DEPENDENCY_CYCLE]")
        if n in memo: return memo[n]
        visiting.add(n); ds=[calc(d) for d in deps[n]]; visiting.remove(n)
        own=standings.get(n,"UNKNOWN")
        if any(x in {"BUILD_BROKEN","BLOCKED"} for x in ds): own="BLOCKED"
        elif any(x=="UNKNOWN" for x in ds) and own=="PARTIAL_ALIVE": own="UNKNOWN"
        memo[n]=own; return own
    return {n:calc(n) for n in sorted(nodes)}
