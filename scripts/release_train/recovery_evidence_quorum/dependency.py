BROKEN={"BUILD_BROKEN","BLOCKED"}
class DependencyGraph:
    def __init__(self,edges=()):
        self.edges={}
        for parent,child in edges:
            self.edges.setdefault(parent,set()).add(child); self.edges.setdefault(child,set())
        self.order()
    def order(self):
        temp=set(); perm=set(); out=[]
        def visit(node):
            if node in temp: raise ValueError("REFUSED[DEPENDENCY_CYCLE]")
            if node in perm:return
            temp.add(node)
            for child in self.edges.get(node,()):visit(child)
            temp.remove(node);perm.add(node);out.append(node)
        for node in sorted(self.edges):visit(node)
        return tuple(out)
    def blockers(self,standing):
        return tuple(sorted(node for node in self.order() if standing.get(node,"UNKNOWN") in BROKEN))
