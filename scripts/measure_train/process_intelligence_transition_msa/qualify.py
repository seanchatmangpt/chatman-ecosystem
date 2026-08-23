from .admission import admit_evidence
from .census import evidence_census
from .discharge import discharge
from .regression import regressions
from .dependency import obligation_dependency_graph
from .blockers import propagated_states
from .standing import standing
from .receipt import manufacture_receipt
from .telemetry import project_transition

def qualify_transition(before_epoch, after_epoch, obligations, before_evidence, after_evidence, dependency_edges, now, parent_receipt=None):
    before = admit_evidence(before_epoch, obligations, before_evidence, now)
    after = admit_evidence(after_epoch, obligations, after_evidence, now)
    before_census = evidence_census(obligations, before)
    after_census = evidence_census(obligations, after)
    discharged = discharge(before_census, after_census, after)
    regressed = regressions(before_census, after_census)
    graph = obligation_dependency_graph(obligations, dependency_edges)
    propagated = propagated_states(after_census, graph)
    status = standing(after_census, propagated)
    receipt = manufacture_receipt(after_epoch, after_census, discharged, regressed, status, parent_receipt)
    return {
        "before_census": before_census,
        "after_census": after_census,
        "discharges": discharged,
        "regressions": regressed,
        "propagated": propagated,
        "standing": status,
        "receipt": receipt,
        "telemetry": project_transition(before_epoch, after_epoch, after_census, discharged, regressed),
        "actuation_performed": False,
    }
