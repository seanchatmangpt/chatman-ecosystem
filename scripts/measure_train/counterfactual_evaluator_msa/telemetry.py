def project(subject,cases,models,standing_value):
    events=[]
    for c in sorted(cases):
        events.append({"activity":"evaluate_counterfactual_estimator","repo":subject.repo,"sha":subject.sha,"estimator_id":c.estimator.estimator_id,"family":c.estimator.family,"case_id":c.case_id,"truth":str(c.truth),"estimate":str(c.estimate),"time":c.observed_at.isoformat()})
    events.append({"activity":"qualify_counterfactual_evaluator","repo":subject.repo,"sha":subject.sha,"standing":standing_value,"model_count":len(models)})
    return tuple(events)
