from .errors import Refused

_HARD = {"BUILD_BROKEN","BLOCKED"}

def blockers(graph, standings):
    visiting, done = set(), set()
    found = set()
    def visit(node):
        if node in visiting:
            raise Refused("DEPENDENCY_CYCLE", node)
        if node in done:
            return
        visiting.add(node)
        if standings.get(node) in _HARD:
            found.add(node)
        for parent in graph.get(node, ()):
            visit(parent)
        visiting.remove(node)
        done.add(node)
    for node in graph:
        visit(node)
    return frozenset(sorted(found))
