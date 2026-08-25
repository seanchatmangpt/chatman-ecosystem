from .refusal import require


def blockers(graph: dict[str,tuple[str,...]], standing: dict[str,str], root: str) -> tuple[str,...]:
    visiting=set(); seen=set(); blocked=set()
    def walk(node:str) -> None:
        require(node not in visiting,"DEPENDENCY_CYCLE",node)
        if node in seen: return
        visiting.add(node)
        for dep in graph.get(node,()):
            if standing.get(dep,'UNKNOWN')!='ALIVE': blocked.add(dep)
            walk(dep)
        visiting.remove(node); seen.add(node)
    walk(root)
    return tuple(sorted(blocked))
