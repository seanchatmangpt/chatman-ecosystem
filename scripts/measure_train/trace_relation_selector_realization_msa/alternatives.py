from .subject import Refused

def observed_alternatives(decision, realizations):
    by_relation={}
    for row in realizations:
        by_relation.setdefault(row.relation,[]).append(row)
    observed=tuple(sorted(r for r in decision.candidates if r in by_relation))
    if any(r not in decision.candidates for r in by_relation):
        raise Refused("REFUSED[REALIZATION_OUTSIDE_CANDIDATE_SET]")
    return observed

def require_observed_counterfactual(relation, observed):
    if relation not in observed:
        raise Refused("REFUSED[UNOBSERVED_COUNTERFACTUAL]")
    return True
