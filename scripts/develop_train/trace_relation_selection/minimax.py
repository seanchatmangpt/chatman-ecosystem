from .wilson import wilson_upper

def select_minimax(evidence):
    scored = []
    for e in evidence:
        worst = max(wilson_upper(e.false_equivalence, e.support), wilson_upper(e.false_refusal, e.support))
        scored.append((worst, e.evaluation_cost, e.relation.value, e.relation))
    return min(scored)[-1] if scored else None
