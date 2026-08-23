def project(plan,outcomes,realization,standing_value):
    events=[]
    for o in sorted(outcomes):
        events.append({"activity":"fusion_acquisition_observe","repo":plan.subject.repo,"sha":plan.subject.sha,"plan_id":plan.plan_id,
                       "sensor_id":o.sensor_id,"evidence_id":o.evidence_id,"cost":o.cost,"latency_ms":o.latency_ms,"time":o.observed_at.isoformat()})
    events.append({"activity":"fusion_acquisition_realize","repo":plan.subject.repo,"sha":plan.subject.sha,"plan_id":plan.plan_id,
                   "predicted_gain_bits":realization.predicted_bits,"realized_gain_bits":realization.realized_bits,"standing":standing_value})
    return tuple(events)
