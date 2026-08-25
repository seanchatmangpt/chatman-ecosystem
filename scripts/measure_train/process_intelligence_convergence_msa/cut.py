def blocking_cut(epoch, dependency_graph):
    states={o.obligation_id:o.state for o in epoch.obligations}
    bad={oid for oid,state in states.items() if state in {"FAIL","REFUSED","BLOCKED","UNKNOWN"}}
    cut=set()
    for node in sorted(states):
        if states[node] == "PASS":
            for parent in dependency_graph.get(node,()):
                if parent in bad: cut.add(parent)
    return tuple(sorted(cut))
