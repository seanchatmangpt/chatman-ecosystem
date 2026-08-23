from .admission import admit
from .dependency import graph
from .cut import blocking_cut
from .convergence import analyze
from .standing import standing
from .receipt import manufacture
from .telemetry import project

def qualify(epochs, dependency_edges, now, ttl_seconds):
    rows=admit(epochs,now,ttl_seconds)
    nodes=[o.obligation_id for o in rows[-1].obligations]
    g=graph(nodes,dependency_edges)
    cut=blocking_cut(rows[-1],g)
    result=analyze(rows)
    status=standing(rows[-1],result,cut)
    receipt=manufacture(rows[-1].subject,result,cut,status)
    return {"convergence":result,"blocking_cut":cut,"standing":status,"receipt":receipt,"telemetry":project(rows,result,cut),"actuation_performed":False}
