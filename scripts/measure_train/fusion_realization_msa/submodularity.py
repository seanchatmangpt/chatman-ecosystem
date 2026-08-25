from .subject import Refused
def submodularity_ratio(sensor_ids, value_fn):
    ids=tuple(sensor_ids)
    if not ids or len(set(ids))!=len(ids): raise Refused("REFUSED[INVALID_SUBMODULAR_SET]")
    base=value_fn(frozenset())
    joint=value_fn(frozenset(ids))-base
    singles=sum(value_fn(frozenset({s}))-base for s in ids)
    if joint <= 0: return 1.0 if singles<=0 else 0.0
    return max(0.0,min(1.0,singles/joint))
