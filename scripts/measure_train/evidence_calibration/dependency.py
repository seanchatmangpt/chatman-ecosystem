from .subject import Refused
def propagate(nodes, edges, standings):
    graph={n:[] for n in nodes}
    for c,p in edges:
        if c not in graph or p not in graph: raise Refused("REFUSED[UNKNOWN_DEPENDENCY]")
        graph[c].append(p)
    visiting=set(); memo={}
    def visit(n):
        if n in visiting: raise Refused("REFUSED[DEPENDENCY_CYCLE]")
        if n in memo:return memo[n]
        visiting.add(n); parents=[visit(p) for p in graph[n]]; visiting.remove(n)
        own=standings.get(n,"UNKNOWN")
        if any(x in {"BUILD_BROKEN","BLOCKED"} for x in parents): own="BLOCKED"
        elif any(x=="UNKNOWN" for x in parents) and own=="PARTIAL_ALIVE": own="UNKNOWN"
        memo[n]=own; return own
    return {n:visit(n) for n in sorted(nodes)}
