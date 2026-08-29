from __future__ import annotations

class Refusal(ValueError):
    pass

def dependency_order(graph: dict[str, tuple[str,...]], selected: set[str]) -> tuple[str,...]:
    for node in selected:
        missing=set(graph.get(node,()))-selected
        if missing:
            raise Refusal(f"REFUSED[DEPENDENCY_GAP]:{node}:{sorted(missing)}")
    order=[]; temporary=set(); permanent=set()
    def visit(node:str)->None:
        if node in permanent:return
        if node in temporary: raise Refusal("REFUSED[DEPENDENCY_CYCLE]")
        temporary.add(node)
        for dep in sorted(graph.get(node,())):
            visit(dep)
        temporary.remove(node); permanent.add(node); order.append(node)
    for node in sorted(selected): visit(node)
    return tuple(order)

def propagate(standing_by_repo: dict[str,str], graph: dict[str,tuple[str,...]], order: tuple[str,...]) -> dict[str,str]:
    out=dict(standing_by_repo)
    for repo in order:
        if any(out.get(dep) in {"BUILD_BROKEN","BLOCKED"} for dep in graph.get(repo,())):
            out[repo]="BLOCKED"
    return out
