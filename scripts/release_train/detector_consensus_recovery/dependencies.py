def topological_order(graph):
    nodes=set(graph) | {d for deps in graph.values() for d in deps}; indegree={n:0 for n in nodes}; children={n:set() for n in nodes}
    for n,deps in graph.items():
        for d in deps: indegree[n]+=1; children[d].add(n)
    ready=sorted(n for n,v in indegree.items() if v==0); out=[]
    while ready:
        n=ready.pop(0); out.append(n)
        for c in sorted(children[n]):
            indegree[c]-=1
            if indegree[c]==0: ready.append(c); ready.sort()
    if len(out)!=len(nodes): raise ValueError("REFUSED[DEPENDENCY_CYCLE]")
    return tuple(out)

def blockers(graph, standing):
    topological_order(graph); red={"BUILD_BROKEN","BLOCKED","UNSUPPORTED"}; result={}
    for n in graph:
        seen=set(); stack=list(graph.get(n,()))
        while stack:
            d=stack.pop()
            if d in seen: continue
            seen.add(d); stack.extend(graph.get(d,()))
        result[n]=tuple(sorted(d for d in seen if standing.get(d,"UNKNOWN") in red))
    return result
