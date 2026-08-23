from .subject import Refused

def graph(nodes, edges):
    g = {node: [] for node in nodes}
    for child, parent in edges:
        if child not in g or parent not in g:
            raise Refused("REFUSED[UNKNOWN_DEPENDENCY]")
        g[child].append(parent)
    visiting, done = set(), set()
    def visit(node):
        if node in visiting:
            raise Refused("REFUSED[DEPENDENCY_CYCLE]")
        if node in done:
            return
        visiting.add(node)
        for parent in g[node]:
            visit(parent)
        visiting.remove(node)
        done.add(node)
    for node in sorted(g):
        visit(node)
    return {key: tuple(sorted(value)) for key, value in sorted(g.items())}
