from .correspondence import admit_correspondence,rail_equivalence
from .distributed import distributed_currentness
from .closure import closure_census
from .standing import standing
from .receipt import manufacture
from .telemetry import project

def qualify(subject,methodology,evidence,regions,now,max_age_seconds=3600,parent=None):
    admitted=admit_correspondence(subject,evidence)
    corr=rail_equivalence(admitted)
    dist=distributed_currentness(subject,regions,now,max_age_seconds)
    census=closure_census(methodology,admitted,dist["state"])
    status=standing(census,corr)
    receipt=manufacture(subject,census,status,parent)
    return {"standing":status,"correspondence":corr,"distributed":dist,"census":census,
            "receipt":receipt,"telemetry":project(subject,admitted,census),"actuation_performed":False}
