from .admission import admit
from .feasibility import evaluate
from .differential import oracle_differential
from .realization import realized
from .calibration import calibrate
from .standing import standing
from .receipt import manufacture
def qualify(subject, rows, now, dependencies=()):
    a=admit(subject,rows,now); f=evaluate(a); d=oracle_differential(a); r=realized(a); c=calibrate(f,d,r); s=standing(c,dependencies)
    return {"feasibility":f,"differential":d,"realization":r,"calibration":c,"standing":s,"receipt":None if s in {"BUILD_BROKEN","BLOCKED"} else manufacture(subject,c,s),"actuation_performed":False}
