from .admission import admit
from .methodology import coverage
from .calibration import calibrate
from .census import census
from .standing import standing
from .receipt import manufacture
from .telemetry import project
from .worst_stratum import worst_stratum
from .capital import effective_capital
from .diversity import diversity
def qualify(subject,observations,now,dependency_states=()):
    rows=admit(subject,observations,now); methods=coverage(o.projection.methodology for o in rows); cal=calibrate(rows); status=standing(rows,cal,methods["complete"],dependency_states); c=census(rows)
    receipt=None if status in {"BUILD_BROKEN","BLOCKED"} else manufacture(subject,c,status)
    return {"standing":status,"calibration":cal,"methodology":methods,"census":c,"worst_stratum":worst_stratum(rows),"effective_capital":effective_capital([o.projection for o in rows]),"diversity":diversity([o.projection for o in rows]),"receipt":receipt,"telemetry":project(subject,rows,status),"actuation_performed":False}
