from .probability import nonnegative

def value_of_information(current_risk, expected_future_risk, evidence_cost):
    return nonnegative(current_risk)-nonnegative(expected_future_risk)-nonnegative(evidence_cost)
