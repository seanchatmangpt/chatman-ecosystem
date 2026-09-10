from .admission import admit_selection
from .contradiction import contradictions
from .drift import classify_drift
from .standing import standing
from .receipt import manufacture_receipt
from .telemetry import project

def qualify(selection, frontier, candidates, now, dependency_states=(), sibling_selections=(), parent_receipt=None):
    selected = admit_selection(selection, frontier, candidates, now)
    conflicts = contradictions((selection, *sibling_selections))
    drift = classify_drift(selection, frontier)
    status = standing(selected, conflicts, dependency_states)
    receipt = manufacture_receipt(selection, selected, drift, status, parent_receipt)
    return {
        "selected": selected,
        "drift": drift,
        "contradictions": conflicts,
        "standing": status,
        "receipt": receipt,
        "telemetry": project(selection, selected, drift, status),
        "actuation_performed": False,
    }
