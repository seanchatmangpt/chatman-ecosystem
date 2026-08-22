from .admission import admit
from .graph import affected_consumers
from .census import acknowledgement_census
from .standing import standing
from .receipt import manufacture_receipt
from .telemetry import project

def qualify(event, bindings, deliveries, acknowledgements, discharges, parent_receipt=None):
    deliveries, acknowledgements, discharges = admit(event,deliveries,acknowledgements,discharges)
    affected=affected_consumers(bindings,event.producer)
    census=acknowledgement_census(event,affected,deliveries,acknowledgements,discharges)
    status=standing(census)
    receipt=manufacture_receipt(event,census,status,parent_receipt)
    return {
        "affected":affected,
        "census":census,
        "standing":status,
        "receipt":receipt,
        "telemetry":project(event,census),
        "actuation_performed":False,
    }
