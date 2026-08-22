from .subject import Refusal
class DependencyGraph:
    def __init__(self, edges):
        self.edges={k:tuple(v) for k,v in edges.items()}
        nodes=set(self.edges)
        for vs in self.edges.values(): nodes.update(vs)
        self.nodes=nodes
        self._order=self._toposort()
    def _toposort(self):
        state={}; out=[]
        def visit(n):
            if state.get(n)==1: raise Refusal('REFUSED[DEPENDENCY_CYCLE]')
            if state.get(n)==2: return
            state[n]=1
            for d in sorted(self.edges.get(n,())): visit(d)
            state[n]=2; out.append(n)
        for n in sorted(self.nodes): visit(n)
        return tuple(out)
    @property
    def order(self): return self._order
    def blocker(self, standings):
        for n in self._order:
            if standings.get(n) in {'BUILD_BROKEN','BLOCKED'}: return n
        return None
