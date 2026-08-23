from .relation import Relation

def deterministic_census(calibrations, perturbations):
    by={c.relation:c for c in calibrations}
    return tuple(
        (r.value, by[r].state if r in by else "UNKNOWN", by[r].support if r in by else 0,
         tuple(perturbations))
        for r in Relation
    )
