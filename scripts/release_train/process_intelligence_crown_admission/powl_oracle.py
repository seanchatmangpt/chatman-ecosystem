from .powl_model import PowlModel

def bounded_traces(model: PowlModel) -> tuple[tuple[str, ...], ...]:
    """Independent bounded state-space oracle for strict-order + cyclic choice reachability."""
    predecessors={n:set() for n in model.activities}
    for a,b in model.strict_order: predecessors[b].add(a)
    choices={n:set() for n in model.activities}
    for a,b in model.choice_edges: choices[a].add(b)
    out=set()
    def walk(current, seen, trace, steps):
        if steps > model.bound: return
        if current == model.terminal:
            out.add(tuple(trace))
            return
        enabled=[]
        for nxt in sorted(choices[current]):
            if predecessors[nxt].issubset(seen): enabled.append(nxt)
        for nxt in enabled:
            walk(nxt, seen | {nxt}, trace+[nxt], steps+1)
    walk(model.start, {model.start}, [model.start], 0)
    return tuple(sorted(out))
