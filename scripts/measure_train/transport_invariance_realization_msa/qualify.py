from .admission import admit_cases
from .confusion import confusion
from .estimators import calibrate_risk
from .frontier import current
from .census import census
from .standing import standing
from .receipt import manufacture
from .telemetry import project
def qualify(subject,cases,models,now,dependency_states=(),drifted=False):
    model=current(models); rows=admit_cases(subject,cases,now,model.generation); conf=confusion(rows); cal=calibrate_risk(rows)
    status=standing(rows,cal.state,conf,dependency_states,drifted); cen=census(rows); receipt=None if status in {"BUILD_BROKEN","BLOCKED"} else manufacture(subject,model,cen,status)
    return {"cases":rows,"confusion":conf,"risk_calibration":cal,"census":cen,"standing":status,"receipt":receipt,"telemetry":project(subject,rows,model,status),"actuation_performed":False}
