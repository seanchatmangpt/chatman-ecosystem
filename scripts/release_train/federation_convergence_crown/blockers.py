from .refusal import refuse
def transitive_blockers(graph,failed):
    out=set(); visiting=set()
    def walk(node):
        if node in visiting: refuse("DEPENDENCY_CYCLE")
        visiting.add(node)
        for parent in graph.get(node,()):
            if parent in failed: out.add(parent)
            walk(parent)
        visiting.remove(node)
    for node in graph: walk(node)
    return tuple(sorted(out))
