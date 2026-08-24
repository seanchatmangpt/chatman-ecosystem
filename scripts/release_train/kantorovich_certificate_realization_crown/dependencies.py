from .refusal import Refused
def blockers(graph, standing):
    visiting=set(); memo={}
    def walk(n):
        if n in visiting: raise Refused('DEPENDENCY_CYCLE')
        if n in memo: return memo[n]
        visiting.add(n); out=set()
        if standing.get(n) in {'BUILD_BROKEN','BLOCKED'}: out.add(n)
        for d in graph.get(n,()): out |= walk(d)
        visiting.remove(n); memo[n]=out; return out
    return walk('root')
