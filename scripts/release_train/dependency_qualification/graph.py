from . import Refusal

def dependency_closure(root: str, edges: dict[str, tuple[str,...]]) -> tuple[str,...]:
    order=[]; visiting=set(); seen=set()
    def visit(node):
        if node in visiting: raise Refusal('REFUSED[DEPENDENCY_CYCLE]')
        if node in seen: return
        visiting.add(node)
        for dep in sorted(edges.get(node, ())): visit(dep)
        visiting.remove(node); seen.add(node); order.append(node)
    visit(root)
    return tuple(order)
