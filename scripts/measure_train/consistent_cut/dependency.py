from .subject import Refused

def dependency_graph(subjects, edges):
    nodes=set(subjects)
    graph={n:[] for n in nodes}
    for consumer, producer in edges:
        if consumer not in nodes or producer not in nodes:
            raise Refused("REFUSED[UNKNOWN_DEPENDENCY]")
        graph[consumer].append(producer)
    visiting=set(); done=set()
    def visit(n):
        if n in visiting:
            raise Refused("REFUSED[DEPENDENCY_CYCLE]")
        if n in done:
            return
        visiting.add(n)
        for p in graph[n]:
            visit(p)
        visiting.remove(n); done.add(n)
    for n in nodes:
        visit(n)
    return {k:tuple(sorted(v)) for k,v in sorted(graph.items())}
