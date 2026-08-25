from .refusal import Refused

def dependency_graph(component_ids, edges):
    g={x:[] for x in component_ids}
    for child,parent in edges:
        if child not in g or parent not in g:
            raise Refused("REFUSED[UNKNOWN_COMPONENT_DEPENDENCY]")
        g[child].append(parent)
    visiting=set(); done=set()
    def visit(n):
        if n in visiting:
            raise Refused("REFUSED[COMPONENT_DEPENDENCY_CYCLE]")
        if n in done: return
        visiting.add(n)
        for p in g[n]: visit(p)
        visiting.remove(n); done.add(n)
    for n in sorted(g): visit(n)
    return {k:tuple(sorted(v)) for k,v in sorted(g.items())}

def propagate(census, graph):
    base={r[0]:r[2] for r in census}
    memo={}
    def state(n):
        if n in memo: return memo[n]
        own=base[n]
        parents=[state(p) for p in graph.get(n,())]
        if own=="EXACT" and any(p in {"DIVERGED","BLOCKED"} for p in parents):
            own="BLOCKED"
        elif own=="EXACT" and any(p in {"CENSORED","UNKNOWN"} for p in parents):
            own="UNKNOWN"
        memo[n]=own
        return own
    return {n:state(n) for n in sorted(base)}
