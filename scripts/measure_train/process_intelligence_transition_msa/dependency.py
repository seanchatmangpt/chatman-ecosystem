from .subject import Refused

def obligation_dependency_graph(obligations, edges):
    ids = {o.obligation_id for o in obligations}
    graph = {oid: [] for oid in ids}
    for consumer, producer in edges:
        if consumer not in ids or producer not in ids:
            raise Refused("REFUSED[UNKNOWN_OBLIGATION_DEPENDENCY]")
        graph[consumer].append(producer)

    visiting, done = set(), set()
    def visit(node):
        if node in visiting:
            raise Refused("REFUSED[OBLIGATION_DEPENDENCY_CYCLE]")
        if node in done:
            return
        visiting.add(node)
        for parent in graph[node]:
            visit(parent)
        visiting.remove(node)
        done.add(node)

    for node in sorted(ids):
        visit(node)
    return {k: tuple(sorted(v)) for k, v in sorted(graph.items())}
