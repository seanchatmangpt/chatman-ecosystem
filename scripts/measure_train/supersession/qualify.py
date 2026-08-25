from .admission import admit
from .frontier import resolve_frontier
from .contradiction import contradictions
from .standing import standing
from .receipt import manufacture_receipt
from .telemetry import project

def qualify(subject, evidence, supersessions, parent_receipt=None):
    admitted = admit(subject, evidence)
    current, historical = resolve_frontier(admitted, supersessions)
    conflicts = contradictions(current)
    status = standing(current, conflicts)
    receipt = manufacture_receipt(subject, current, historical, status, parent_receipt)
    return {
        "subject": subject,
        "current": current,
        "historical": historical,
        "contradictions": conflicts,
        "standing": status,
        "receipt": receipt,
        "telemetry": project(subject, current, historical),
        "actuation_performed": False,
    }
