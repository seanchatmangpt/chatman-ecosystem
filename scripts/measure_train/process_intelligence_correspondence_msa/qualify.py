from .correspondence import admit_correspondence
from .trace import trace_equivalence
from .methodology import coverage
from .census import census
from .standing import standing
from .receipt import manufacture
def qualify(subject, rails, methodologies, oracle_state, region_state, authority_state):
    admitted=admit_correspondence(subject,rails)
    trace=trace_equivalence(admitted)
    c=census(admitted,coverage(methodologies),oracle_state,region_state,authority_state)
    c["trace_equivalence"]=trace
    status=standing(c)
    r=manufacture(subject,c,status)
    return {"standing":status,"census":c,"receipt":r,"actuation_performed":False}
