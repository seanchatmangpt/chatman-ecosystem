def blocker_cut(nodes, graph):
    state={n.evidence_id:n.state for n in nodes}
    bad={k for k,v in state.items() if v in {"FAIL","REFUSED","UNKNOWN"}}
    cut=set()
    for child,parents in graph.items():
        if state.get(child)=="PASS":
            cut.update(p for p in parents if p in bad)
    return tuple(sorted(cut))
