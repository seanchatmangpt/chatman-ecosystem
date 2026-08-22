from collections import deque
from .subject import Refused

def affected_consumers(bindings, producer):
    edges={}
    nodes={producer}
    for upstream,downstream in bindings:
        edges.setdefault(upstream,[]).append(downstream)
        nodes.add(upstream); nodes.add(downstream)
    visiting=set(); done=set()
    def visit(n):
        if n in visiting:
            raise Refused("REFUSED[DEPENDENCY_CYCLE]")
        if n in done:
            return
        visiting.add(n)
        for child in edges.get(n,()):
            visit(child)
        visiting.remove(n); done.add(n)
    for n in tuple(nodes): visit(n)

    q=deque([(producer,0)]); seen={producer}; out=[]
    while q:
        node,depth=q.popleft()
        for child in sorted(edges.get(node,())):
            if child not in seen:
                seen.add(child); q.append((child,depth+1)); out.append((child,depth+1))
    return tuple(out)
