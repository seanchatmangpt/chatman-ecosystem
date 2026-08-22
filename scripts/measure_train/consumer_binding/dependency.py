from .subject import Refused

def propagate_consumer_standing(nodes, edges, standings):
    deps = {node: [] for node in nodes}
    for consumer, producer in edges:
        if consumer not in deps or producer not in deps:
            raise Refused("REFUSED[UNKNOWN_DEPENDENCY]")
        deps[consumer].append(producer)

    visiting, memo = set(), {}
    def calc(node):
        if node in visiting:
            raise Refused("REFUSED[DEPENDENCY_CYCLE]")
        if node in memo:
            return memo[node]
        visiting.add(node)
        parents = [calc(dep) for dep in deps[node]]
        visiting.remove(node)
        own = standings.get(node, "UNKNOWN")
        if any(v in {"BUILD_BROKEN","BLOCKED"} for v in parents):
            own = "BLOCKED"
        elif any(v == "UNKNOWN" for v in parents) and own == "PARTIAL_ALIVE":
            own = "UNKNOWN"
        memo[node] = own
        return own

    return {node: calc(node) for node in sorted(nodes)}
