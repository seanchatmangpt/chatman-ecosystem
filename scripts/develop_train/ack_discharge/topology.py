from collections import deque
from dataclasses import dataclass
from .subject import Subject
class RefusedTopology(ValueError): pass
@dataclass(frozen=True,slots=True)
class ConsumerNode: subject:Subject; critical:bool=False
class DependencyTopology:
 def __init__(self,producer,consumers,edges):
  self.producer=producer; self.nodes={n.subject.identity:n for n in consumers}; self.edges={k:[] for k in [producer.identity,*self.nodes]}
  if len(self.nodes)!=len(consumers): raise RefusedTopology('REFUSED[DUPLICATE_CONSUMER]')
  for a,b in edges:
   if a not in self.edges or b not in self.nodes: raise RefusedTopology('REFUSED[UNKNOWN_DEPENDENCY_NODE]')
   self.edges[a].append(b)
  self._acyclic()
 def _acyclic(self):
  seen=set(); active=set()
  def visit(n):
   if n in active: raise RefusedTopology('REFUSED[DEPENDENCY_CYCLE]')
   if n in seen:return
   active.add(n)
   for c in self.edges.get(n,[]): visit(c)
   active.remove(n);seen.add(n)
  visit(self.producer.identity)
 def affected(self):
  out=[];q=deque([(self.producer.identity,0)]);seen={self.producer.identity}
  while q:
   p,d=q.popleft()
   for c in sorted(self.edges.get(p,[])):
    if c in seen:continue
    seen.add(c);out.append((self.nodes[c],d+1));q.append((c,d+1))
  return out
