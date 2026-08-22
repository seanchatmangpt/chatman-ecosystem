class GraphRefusal(ValueError): pass
class DependencyGraph:
    def __init__(self, edges=()):
        self.edges=tuple(edges)
    def order(self, selected):
        selected=set(selected)
        deps={n:set() for n in selected}
        for child,parent in self.edges:
            if child in selected:
                if parent not in selected: raise GraphRefusal("REFUSED[DEPENDENCY_NOT_CLOSED]")
                deps[child].add(parent)
        out=[]
        while deps:
            ready=sorted(n for n,d in deps.items() if not d)
            if not ready: raise GraphRefusal("REFUSED[DEPENDENCY_CYCLE]")
            for n in ready:
                out.append(n); deps.pop(n)
            for d in deps.values(): d.difference_update(ready)
        return tuple(out)
