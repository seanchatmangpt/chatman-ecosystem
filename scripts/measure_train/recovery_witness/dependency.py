from .subject import Refused

def propagate(nodes, edges, standings):
    graph={n:[] for n in nodes}
    for consumer, producer in edges:
        if consumer not in graph or producer not in graph:
            raise Refused("REFUSED[UNKNOWN_DEPENDENCY]")
        graph[consumer].append(producer)
    visiting=set(); memo={}
    def calc(n):
        if n in visiting: raise Refused("REFUSED[DEPENDENCY_CYCLE]")
        if n in memo: return memo[n]
        visiting.add(n); deps=[calc(x) for x in graph[n]]; visiting.remove(n)
        own=standings.get(n,"UNKNOWN")
        if any(x in {"BUILD_BROKEN","BLOCKED"} for x in deps): own="BLOCKED"
        elif any(x=="UNKNOWN" for x in deps) and own=="PARTIAL_ALIVE": own="UNKNOWN"
        memo[n]=own; return own
    return {n:calc(n) for n in sorted(nodes)}
