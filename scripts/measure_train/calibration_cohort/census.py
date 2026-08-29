from .subject import Refused
def census(cohort, observations):
    epochs=cohort.by_source(); rows=[]
    grouped={s:[] for s in epochs}
    for o in observations:
        if o.source not in epochs: raise Refused("REFUSED[FOREIGN_OBSERVATION_SOURCE]")
        if o.epoch_generation!=epochs[o.source].generation: raise Refused("REFUSED[STALE_OBSERVATION_GENERATION]")
        grouped[o.source].append(o.outcome)
    for source, outcomes in sorted(grouped.items()):
        if not outcomes: state="UNKNOWN"
        elif "FAIL" in outcomes: state="FAIL"
        elif "PENDING" in outcomes or "UNKNOWN" in outcomes: state="UNKNOWN"
        elif set(outcomes)=={"UNSUPPORTED"}: state="UNSUPPORTED"
        elif set(outcomes)=={"PASS"}: state="PASS"
        else: state="CONTRADICTED"
        rows.append((source,state))
    return tuple(rows)
