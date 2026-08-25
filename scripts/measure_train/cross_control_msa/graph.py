from .refusal import Refused
def admit_graph(nodes,edges):
 g={n:[] for n in nodes}
 for c,p in edges:
  if c not in g or p not in g: raise Refused("REFUSED[UNKNOWN_CONTROL_DEPENDENCY]")
  g[c].append(p)
 seen=set(); active=set()
 def visit(n):
  if n in active: raise Refused("REFUSED[CONTROL_DEPENDENCY_CYCLE]")
  if n in seen:return
  active.add(n)
  for p in g[n]:visit(p)
  active.remove(n);seen.add(n)
 for n in sorted(g):visit(n)
 return {k:tuple(sorted(v)) for k,v in sorted(g.items())}
