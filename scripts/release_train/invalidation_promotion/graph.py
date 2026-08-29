from collections import defaultdict, deque
from .subject import Refusal

class DependencyGraph:
    def __init__(self, bindings):
        self.bindings = tuple(bindings)
        self.children = defaultdict(list)
        self.nodes = set()
        for b in self.bindings:
            self.nodes.update((b.producer.key, b.consumer.key))
            self.children[b.producer.key].append(b.consumer.key)
        self._assert_acyclic()
    def _assert_acyclic(self):
        indeg = {n:0 for n in self.nodes}
        for children in self.children.values():
            for dst in children:
                indeg[dst] += 1
        q = deque(sorted(n for n,d in indeg.items() if d == 0))
        seen = []
        while q:
            n=q.popleft(); seen.append(n)
            for child in sorted(self.children.get(n,())):
                indeg[child]-=1
                if indeg[child]==0:
                    q.append(child)
        if len(seen)!=len(self.nodes):
            raise Refusal('REFUSED[DEPENDENCY_CYCLE]')
    def descendants(self, producer_key):
        depth={producer_key:0}; q=deque([producer_key]); out=[]
        while q:
            current=q.popleft()
            for child in sorted(self.children.get(current,())):
                if child not in depth:
                    depth[child]=depth[current]+1
                    out.append((child,depth[child])); q.append(child)
        return tuple(out)
