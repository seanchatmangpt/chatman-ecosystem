from fractions import Fraction
from .transport import TransportPlan
from .errors import Refused

def solve_primal(source, target, metric):
    source_mass = source.as_dict(); target_mass = target.as_dict()
    flows = {(left, right): Fraction(0) for left in source_mass for right in target_mass}
    remaining_source = dict(source_mass); remaining_target = dict(target_mass)
    while any(value > 0 for value in remaining_source.values()):
        nodes = [("S", key) for key in source_mass] + [("T", key) for key in target_mass]
        dist = {node: None for node in nodes}; prev = {}
        for key, value in remaining_source.items():
            if value > 0:
                dist[("S", key)] = Fraction(0)
        for _ in range(len(nodes) - 1):
            changed = False
            for left in source_mass:
                for right in target_mass:
                    snode = ("S", left); tnode = ("T", right); cost = metric.cost(left, right)
                    if remaining_source[left] > 0 and dist[snode] is not None and (dist[tnode] is None or dist[tnode] > dist[snode] + cost):
                        dist[tnode] = dist[snode] + cost; prev[tnode] = (snode, (left, right), 1); changed = True
                    if flows[(left, right)] > 0 and dist[tnode] is not None and (dist[snode] is None or dist[snode] > dist[tnode] - cost):
                        dist[snode] = dist[tnode] - cost; prev[snode] = (tnode, (left, right), -1); changed = True
            if not changed:
                break
        sinks = [(("T", key), dist[("T", key)]) for key, value in remaining_target.items() if value > 0 and dist[("T", key)] is not None]
        if not sinks:
            raise Refused("NO_TRANSPORT_AUGMENTING_PATH")
        sink = min(sinks, key=lambda item: (item[1], item[0]))[0]
        path = []; node = sink; seen = set()
        while node in prev and node not in seen:
            seen.add(node); edge = prev[node]; path.append(edge); node = edge[0]
        start = node
        if start[0] != "S" or remaining_source[start[1]] <= 0:
            raise Refused("INVALID_RESIDUAL_PATH")
        delta = min(remaining_source[start[1]], remaining_target[sink[1]])
        for _, edge, direction in path:
            if direction < 0:
                delta = min(delta, flows[edge])
        if delta <= 0:
            raise Refused("ZERO_AUGMENTATION")
        for _, edge, direction in path:
            flows[edge] += delta * direction
        remaining_source[start[1]] -= delta; remaining_target[sink[1]] -= delta
    plan = TransportPlan(tuple((a, b, value) for (a, b), value in sorted(flows.items()) if value))
    plan.verify_marginals(source, target)
    return plan
