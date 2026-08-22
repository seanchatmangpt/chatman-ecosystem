def topo(deps:dict[str,set[str]])->list[str]:
    nodes=set(deps)
    for ds in deps.values(): nodes |= set(ds)
    missing=[d for ds in deps.values() for d in ds if d not in deps]
    if missing: raise ValueError("REFUSED[INCOMPLETE_DEPENDENCY_GRAPH]")
    out=[]; temp=set(); perm=set()
    def visit(n):
        if n in temp: raise ValueError("REFUSED[DEPENDENCY_CYCLE]")
        if n in perm:return
        temp.add(n)
        for d in sorted(deps[n]): visit(d)
        temp.remove(n); perm.add(n); out.append(n)
    for n in sorted(nodes): visit(n)
    return out
def propagate(order:list[str], standing:dict[str,str], deps:dict[str,set[str]])->dict[str,str]:
    result=dict(standing)
    for n in order:
        if any(result.get(d) in {"BUILD_BROKEN","BLOCKED","UNKNOWN","UNSUPPORTED"} for d in deps[n]):
            result[n]="BLOCKED"
    return result
