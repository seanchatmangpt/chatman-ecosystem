from .refusal import Refused

HARD={"BUILD_BROKEN","BLOCKED"}

def blockers(graph: dict[str, tuple[str,...]], standing: dict[str,str], root: str) -> tuple[str,...]:
    visiting=set(); seen=set(); bad=set()
    def walk(node):
        if node in visiting: raise Refused("DEPENDENCY_CYCLE", node)
        if node in seen: return
        visiting.add(node)
        for dep in graph.get(node,()):
            if standing.get(dep,"UNKNOWN") in HARD: bad.add(dep)
            walk(dep)
        visiting.remove(node); seen.add(node)
    walk(root)
    return tuple(sorted(bad))
