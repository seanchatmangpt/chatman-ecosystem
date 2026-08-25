from .graph import admit_graph
from .frontier import current
from .census import census
from .standing import standing
from .receipt import manufacture
from .telemetry import project
def qualify(subject,evidence,validators,stats,calibration,models,robustness,dependency_states=(),drift_alarm=False):
    graph=admit_graph(tuple(evidence)); model=current(tuple(models))
    c=census(graph,tuple(validators),stats,calibration,robustness)
    s=standing(calibration,model,dependency_states,drift_alarm,robustness)
    r=manufacture(subject,model,c,s)
    return {"graph":graph,"model":model,"census":c,"standing":s,"receipt":r,"telemetry":project(subject,model,c,s),"actuation_performed":False}
