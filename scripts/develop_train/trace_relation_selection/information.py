from math import log2

def binary_entropy(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -(p * log2(p) + (1-p) * log2(1-p))

def select_information_seeking(evidence):
    if not evidence:
        return None
    def uncertainty(e):
        p = (e.false_equivalence + e.false_refusal) / (2 * e.support)
        return (binary_entropy(p), -float(e.evaluation_cost), e.relation.value)
    return max(evidence, key=uncertainty).relation
