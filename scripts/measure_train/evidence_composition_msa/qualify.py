from .graph import admit_graph
from .blockers import blocker_cut
from .methodology import methodology_coverage
from .bounded_standing import standing
from .receipt import manufacture
from .telemetry import project
def qualify(subject,nodes,edges,calibration,methodology_kinds):
    graph=admit_graph(tuple(nodes),tuple(edges))
    cut=blocker_cut(tuple(nodes),graph)
    mc=methodology_coverage(methodology_kinds)
    status=standing(tuple(nodes),calibration,mc["complete"],cut)
    receipt=manufacture(subject,calibration,cut,status)
    return {"graph":graph,"blocking_cut":cut,"methodology":mc,"standing":status,
            "receipt":receipt,"telemetry":project(subject,calibration,cut,status),
            "actuation_performed":False}
