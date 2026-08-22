from collections import defaultdict

def contradictions(evidence):
    grouped = defaultdict(set)
    for item in evidence:
        grouped[(item.kind, item.scope, item.epoch)].add(item.outcome)
    return tuple(sorted(
        (kind, scope, epoch.sequence, tuple(sorted(outcomes)))
        for (kind, scope, epoch), outcomes in grouped.items()
        if len(outcomes) > 1
    ))
