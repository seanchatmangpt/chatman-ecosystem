from fractions import Fraction

COST={"PASS":0,"UNSUPPORTED":1,"UNKNOWN":2,"REFUSED":3,"BLOCKED":4,"FAIL":5}

def closure_potential(epoch):
    total=sum(o.weight for o in epoch.obligations)
    if total == 0: return Fraction(0)
    debt=sum(COST[o.state]*o.weight for o in epoch.obligations)
    return Fraction(debt,total)

def potential_delta(before, after):
    return closure_potential(after)-closure_potential(before)
