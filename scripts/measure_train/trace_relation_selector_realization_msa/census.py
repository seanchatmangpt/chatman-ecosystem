from .calibration import calibrate
from .stability import churn

def deterministic_census(decisions, realized_losses, dependencies=()):
    ordered=tuple(sorted(decisions,key=lambda d:(d.decided_at,d.decision_id)))
    predicted=[d.predicted_error_ppm for d in ordered]
    realized=[bool(realized_losses.get(d.decision_id,0)) for d in ordered]
    calibration=calibrate(predicted,realized)
    return {
        "decision_count":len(ordered),
        "selector_generations":tuple(sorted({(d.selector.selector.value,d.selector.generation) for d in ordered})),
        "churn":churn(ordered),
        "calibration":calibration,
        "dependencies":tuple(sorted(dependencies)),
    }
