def project(subject,policy,census_result,standing_value):
    return (
        {"activity":"independence_decision_realization_measured","repo":subject.repo,"sha":subject.sha,"policy_id":policy.policy_id,"generation":policy.generation,"support":census_result["support"]},
        {"activity":"independence_decision_realization_qualified","repo":subject.repo,"sha":subject.sha,"standing":standing_value,"actuation_performed":False},
    )
