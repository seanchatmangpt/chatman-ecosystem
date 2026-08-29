from dataclasses import dataclass
from .authority import ActionClass,admit_action
from .dependency import blockers as find_blockers
from .pareto import frontier
from .state_machine import classify
from .standing import standing
from .strategy import select
from .receipt import make_receipt
@dataclass(frozen=True)
class Qualification:
    state:str; standing:str; selected:object; blockers:tuple; receipt:object
def qualify(*,subject,identity,expected_identity,step,policy,confidence,budget,calibration,debt,graph,dependency_standing,candidates,strategy):
    admit_action(ActionClass.SELECT); current=identity==expected_identity; calibration_ok=True
    try: calibration.admit()
    except Exception: calibration_ok=False
    blocked=find_blockers(graph,dependency_standing,"release")
    state=classify(step=step,policy=policy,confidence=confidence,budget=budget,calibration_ok=calibration_ok,current=current,blockers=blocked,debt=debt)
    choice=select(frontier(candidates),strategy) if state in {"READY","ACQUIRING"} else None
    s=standing(state)
    body={"schema":"chatman.sequential-horizon-admission/1","subject":subject.value,"controller_generation":identity.generation,"calibration_generation":identity.calibration_generation,"step":step,"state":str(state),"standing":s,"selected":getattr(choice,"name",None),"blockers":list(blocked),"authority":"SELECT","phases":["VERIFY","CONSTRUCT"],"actuation_performed":False}
    return Qualification(str(state),s,choice,blocked,make_receipt(body))
