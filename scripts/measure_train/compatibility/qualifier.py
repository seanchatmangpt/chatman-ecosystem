from .admission import admit
from .compatibility import standing
from .receipt import make_receipt
def qualify(vector, parent=None):
    a=admit(vector)
    if not a["admitted"]: return a
    s=standing(vector)
    axes=[f"{r.axis.value}:{r.outcome.value}" for r in vector.rows]
    return {"admitted":True,"standing":s,"receipt":make_receipt(vector.subject,s,axes,parent),"actuation_performed":False}
