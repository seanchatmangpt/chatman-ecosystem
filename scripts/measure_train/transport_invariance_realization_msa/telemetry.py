def project(subject,cases,model,standing_value):
    events=[{"activity":"transport_invariance_realization_case","repo":subject.repo,"sha":subject.sha,"case_id":c.case_id,"stress":c.stress.kind,"magnitude":str(c.stress.magnitude),"success":c.observed_success,"methodology":c.methodology,"engine":c.engine,"region":c.region,"evidence_root":c.evidence_root} for c in sorted(cases)]
    events.append({"activity":"transport_invariance_realization_qualified","repo":subject.repo,"sha":subject.sha,"model_generation":model.generation,"standing":standing_value})
    return tuple(events)
