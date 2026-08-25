def propagated_states(census, graph):
    base = {row[0]: row[3] for row in census}
    memo = {}
    def state(node):
        if node in memo:
            return memo[node]
        own = base.get(node, "UNKNOWN")
        parents = [state(p) for p in graph.get(node, ())]
        if own == "PASS" and any(p in {"FAIL","REFUSED","BLOCKED"} for p in parents):
            own = "BLOCKED"
        elif own == "PASS" and any(p == "UNKNOWN" for p in parents):
            own = "UNKNOWN"
        memo[node] = own
        return own
    return {node: state(node) for node in sorted(base)}
