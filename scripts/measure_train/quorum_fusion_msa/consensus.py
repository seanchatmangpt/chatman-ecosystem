from .subject import Refused
def consensus(calibrations, independent_pairs, min_independent_pairs=1):
    ids={c.sensor_id for c in calibrations}
    edges={e for e in independent_pairs if e[0] in ids and e[1] in ids}
    if len(edges)<min_independent_pairs:
        raise Refused("REFUSED[INSUFFICIENT_INDEPENDENT_SENSOR_DIVERSITY]")
    score=sum(1.0-c.false_current_rate-c.false_stale_rate-c.ambiguity_rate for c in calibrations)/len(calibrations)
    return {"score":score,"pairs":tuple(sorted(edges))}
