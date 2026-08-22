from .admission import admit_event
from .cascade import cascade
from .state import classify_binding, aggregate
from .receipt import manufacture_receipt
from .telemetry import project

def qualify(bindings, event):
    matched=admit_event(bindings,event)
    cascaded=cascade(bindings,event)
    states=[classify_binding(b,event) for b in matched]
    standing=aggregate(states)
    receipt=manufacture_receipt(event,cascaded,standing)
    return {
        "matched":matched,
        "cascade":cascaded,
        "standing":standing,
        "receipt":receipt,
        "telemetry":project(event,cascaded),
        "actuation_performed":False,
    }
