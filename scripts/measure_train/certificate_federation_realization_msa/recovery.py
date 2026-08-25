def classify(before_relation, after_relation):
    if before_relation == "CENSORED" and after_relation == "EXACT":
        return "OBSERVABILITY_RECOVERED"
    if before_relation == "DIVERGED" and after_relation == "EXACT":
        return "SEMANTIC_REPAIR"
    if before_relation == after_relation:
        return "UNCHANGED"
    return "TRANSITION"
