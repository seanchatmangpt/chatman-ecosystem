from .subject import Refused
def check_gamma_monotonicity(bounds):
    rows=sorted(bounds,key=lambda b:b.gamma)
    for a,b in zip(rows,rows[1:]):
        if b.gamma < a.gamma: raise Refused("REFUSED[GAMMA_ORDER]")
        if b.lower > a.lower or b.upper < a.upper:
            raise Refused("REFUSED[NON_MONOTONE_SENSITIVITY_BOUND]")
    return True
