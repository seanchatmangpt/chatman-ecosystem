from .subject import Refused
def observed_regret(selected_id, realized_values):
    values=dict(realized_values)
    if selected_id not in values or not values: raise Refused("REFUSED[UNOBSERVED_COUNTERFACTUAL]")
    return max(values.values())-values[selected_id]
