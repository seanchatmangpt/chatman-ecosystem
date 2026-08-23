from .subject import Refused
from .relation import Relation

def require_stutter_law(base_activity, stuttered_activity, observed_relation):
    reduced=[]
    for item in stuttered_activity:
        if not reduced or reduced[-1]!=item:
            reduced.append(item)
    if tuple(reduced)!=tuple(base_activity) or observed_relation not in {Relation.STUTTER,Relation.ACTIVITY}:
        raise Refused("REFUSED[STUTTER_METAMORPHIC_VIOLATION]")
    return True

def require_commutation_law(left, right, independent_pairs, observed_relation):
    if sorted(left)!=sorted(right):
        raise Refused("REFUSED[EVENT_MULTIPLICITY_DRIFT]")
    moved={(a,b) for a,b in zip(left,right) if a!=b}
    if moved and not independent_pairs:
        raise Refused("REFUSED[UNPROVEN_EVENT_INDEPENDENCE]")
    if observed_relation not in {Relation.PARTIAL_ORDER,Relation.ACTIVITY,Relation.EXACT}:
        raise Refused("REFUSED[PARTIAL_ORDER_METAMORPHIC_VIOLATION]")
    return True
