from .subject import Refused

def propagate(nodes, edges, standings):
    deps = {node: [] for node in nodes}
    for node, dependency in edges:
        if node not in deps or dependency not in deps:
            raise Refused("REFUSED[UNKNOWN_DEPENDENCY]")
        deps[node].append(dependency)
    visiting, memo = set(), {}
    def visit(node):
        if node in visiting:
            raise Refused("REFUSED[DEPENDENCY_CYCLE]")
        if node in memo:
            return memo[node]
        visiting.add(node)
        inherited = [visit(dep) for dep in deps[node]]
        visiting.remove(node)
        own = standings.get(node, "UNKNOWN")
        if any(value in {"BUILD_BROKEN", "BLOCKED"} for value in inherited):
            own = "BLOCKED"
        elif any(value == "UNKNOWN" for value in inherited) and own == "PARTIAL_ALIVE":
            own = "UNKNOWN"
        memo[node] = own
        return own
    return {node: visit(node) for node in sorted(nodes)}
