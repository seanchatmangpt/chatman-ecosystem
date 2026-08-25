from .admission import admit
from .census import census
from .standing import standing
from .receipt import manufacture
from .telemetry import project
from .regret import observed_regret
from .voi import realized_voi

def qualify(subject,policy,observations,now,dependency_states=(),drifted=False,alternatives=(),defer_realizations=()):
    rows=admit(subject,policy,observations,now)
    c=census(policy,rows); r=observed_regret(policy,rows,alternatives); v=realized_voi(defer_realizations)
    status=standing(c,drifted,dependency_states)
    receipt=manufacture(subject,policy,c,status,v,r)
    return {"census":c,"regret":r,"voi":v,"standing":status,"receipt":receipt,"telemetry":project(subject,policy,c,status),"actuation_performed":False}
