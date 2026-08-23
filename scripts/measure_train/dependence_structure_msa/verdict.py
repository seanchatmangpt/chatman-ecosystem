from dataclasses import dataclass

@dataclass(frozen=True)
class DependenceThresholds:
    min_support:int=8
    max_independent_phi:float=0.10
    max_independent_mi:float=0.02
    max_independent_p:float=0.20
    min_dependent_phi:float=0.35
    min_dependent_mi:float=0.08
    max_dependent_p:float=0.05

def classify(support, absolute_phi, mi, p_value, thresholds=DependenceThresholds()):
    if support < thresholds.min_support:
        return "INSUFFICIENT"
    if absolute_phi <= thresholds.max_independent_phi and mi <= thresholds.max_independent_mi and p_value >= thresholds.max_independent_p:
        return "INDEPENDENT"
    if absolute_phi >= thresholds.min_dependent_phi and mi >= thresholds.min_dependent_mi and p_value <= thresholds.max_dependent_p:
        return "DEPENDENT"
    return "UNKNOWN"
