from .subject import Refused
def brier_score(predicted, actual_index):
    p=tuple(float(x) for x in predicted)
    if not p or actual_index<0 or actual_index>=len(p): raise Refused("REFUSED[INVALID_BRIER_INPUT]")
    if abs(sum(p)-1.0)>1e-9 or any(x<0 or x>1 for x in p): raise Refused("REFUSED[INVALID_BRIER_PROBABILITY]")
    return sum((x-(1.0 if i==actual_index else 0.0))**2 for i,x in enumerate(p))/len(p)
