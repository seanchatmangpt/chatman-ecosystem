from .subject import Refused
def admit_realization(plan,outcomes,sensors,frontier,calibration,cusum):
    if plan.frontier_digest != frontier.digest: raise Refused("REFUSED[STALE_PLAN_FRONTIER]")
    sensor_map={s.sensor_id:s for s in sensors}
    if set(plan.sensor_ids)!=set(sensor_map): raise Refused("REFUSED[SENSOR_SET_DRIFT]")
    seen=set()
    for o in outcomes:
        if o.subject!=plan.subject or o.plan_id!=plan.plan_id: raise Refused("REFUSED[FOREIGN_OUTCOME]")
        if o.sensor_id not in sensor_map: raise Refused("REFUSED[UNPLANNED_SENSOR]")
        if o.evidence_id in seen: raise Refused("REFUSED[DUPLICATE_EVIDENCE]")
        if o.observed_at < plan.issued_at: raise Refused("REFUSED[OUTCOME_PREDATES_PLAN]")
        seen.add(o.evidence_id)
    if calibration.status!="CALIBRATED": raise Refused("REFUSED[UNCALIBRATED_GAIN_MODEL]")
    if cusum.drifted: raise Refused("REFUSED[GAIN_MODEL_DRIFTED]")
    return tuple(sorted(outcomes))
