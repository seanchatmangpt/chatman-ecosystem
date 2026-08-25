def classify(previous_state, current_state):
    if previous_state=="CENSORED" and current_state=="EXACT":
        return "OBSERVABILITY_RECOVERED"
    if previous_state=="DIVERGED" and current_state=="EXACT":
        return "SEMANTIC_REPAIR"
    if previous_state=="EXACT" and current_state=="CENSORED":
        return "OBSERVABILITY_REGRESSION"
    if previous_state=="EXACT" and current_state=="DIVERGED":
        return "SEMANTIC_REGRESSION"
    if previous_state==current_state:
        return "UNCHANGED"
    return "TRANSITION"
