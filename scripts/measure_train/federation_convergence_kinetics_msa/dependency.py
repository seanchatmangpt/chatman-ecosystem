from .refusal import Refused

def graph(nodes, edges):
    adjacency = {node: [] for node in nodes}
    for child, parent in edges:
        if child not in adjacency or parent not in adjacency:
            raise Refused("UNKNOWN_DEPENDENCY")
        adjacency[child].append(parent)
    visiting, done = set(), set()
    def visit(node):
        if node in visiting:
            raise Refused("DEPENDENCY_CYCLE")
        if node in done:
            return
        visiting.add(node)
        for parent in adjacency[node]:
            visit(parent)
        visiting.remove(node)
        done.add(node)
    for node in sorted(adjacency):
        visit(node)
    return {key: tuple(sorted(value)) for key, value in sorted(adjacency.items())}

def propagated(states, adjacency):
    memo = {}
    def state(node):
        if node in memo:
            return memo[node]
        own = states.get(node, "UNKNOWN")
        parents = [state(parent) for parent in adjacency.get(node, ())]
        if any(parent in {"BUILD_BROKEN", "REFUSED"} for parent in parents):
            own = "BUILD_BROKEN"
        elif any(parent == "BLOCKED" for parent in parents):
            own = "BLOCKED"
        elif own == "PARTIAL_ALIVE" and any(parent == "UNKNOWN" for parent in parents):
            own = "UNKNOWN"
        memo[node] = own
        return own
    return {node: state(node) for node in sorted(adjacency)}
