class ProvenanceGraph:
    def __init__(self, edges=()):
        self.edges={a:set() for a,b in edges}
        for a,b in edges: self.edges.setdefault(a,set()).add(b); self.edges.setdefault(b,set())
        self._check()
    def _check(self):
        seen=set(); stack=set()
        def dfs(n):
            if n in stack: raise ValueError("REFUSED[PROVENANCE_CYCLE]")
            if n in seen:return
            stack.add(n)
            for m in self.edges.get(n,()): dfs(m)
            stack.remove(n); seen.add(n)
        for n in list(self.edges): dfs(n)
    def derives(self,a,b):
        todo=list(self.edges.get(a,())); seen=set()
        while todo:
            n=todo.pop()
            if n==b:return True
            if n not in seen: seen.add(n); todo.extend(self.edges.get(n,()))
        return False
