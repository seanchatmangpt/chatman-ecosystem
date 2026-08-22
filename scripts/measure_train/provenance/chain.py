from .subject import Refused

def validate_chain(claim_ids, edges):
    ids=set(claim_ids); parents={}
    for e in edges:
        if e.child_id not in ids or e.parent_id not in ids: raise Refused("REFUSED[ORPHAN_PROVENANCE_EDGE]")
        parents.setdefault(e.child_id,[]).append(e.parent_id)
    visiting=set(); done=set()
    def visit(n):
        if n in visiting: raise Refused("REFUSED[PROVENANCE_CYCLE]")
        if n in done: return
        visiting.add(n)
        for p in parents.get(n,()): visit(p)
        visiting.remove(n); done.add(n)
    for n in ids: visit(n)
    return tuple(sorted((e.child_id,e.parent_id,e.relation) for e in edges))
