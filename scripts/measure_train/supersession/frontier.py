from .subject import Refused

def resolve_frontier(evidence, supersessions):
    by_id = {item.source_id: item for item in evidence}
    superseded = set()
    parents = {}
    for edge in supersessions:
        if edge.newer_id not in by_id or edge.older_id not in by_id:
            raise Refused("REFUSED[ORPHAN_SUPERSESSION_EDGE]")
        newer = by_id[edge.newer_id]
        older = by_id[edge.older_id]
        if newer.kind != older.kind or newer.scope != older.scope:
            raise Refused("REFUSED[INCOMPATIBLE_SUPERSESSION]")
        if newer.epoch <= older.epoch:
            raise Refused("REFUSED[NON_FORWARD_SUPERSESSION]")
        parents.setdefault(edge.newer_id, set()).add(edge.older_id)
        superseded.add(edge.older_id)
    visiting, done = set(), set()
    def visit(node):
        if node in visiting:
            raise Refused("REFUSED[SUPERSESSION_CYCLE]")
        if node in done:
            return
        visiting.add(node)
        for parent in parents.get(node, ()):
            visit(parent)
        visiting.remove(node)
        done.add(node)
    for node in by_id:
        visit(node)
    current = tuple(sorted(item for item in evidence if item.source_id not in superseded))
    historical = tuple(sorted(item for item in evidence if item.source_id in superseded))
    return current, historical
