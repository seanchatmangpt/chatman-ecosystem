def project(decisions, regret_values, standing_value):
    values=tuple(regret_values)
    events=[]
    for decision in sorted(decisions,key=lambda d:(d.decided_at,d.decision_id)):
        events.append({"activity":"trace_relation_selector_decision","repo":decision.subject.repo,"sha":decision.subject.sha,"selector":decision.selector.selector.value,"generation":decision.selector.generation,"decision_id":decision.decision_id,"chosen":[r.value for r in decision.chosen]})
    events.append({"activity":"trace_relation_selector_realization_msa","decision_count":len(decisions),"max_observed_regret":max(values,default=0),"standing":standing_value})
    return tuple(events)
