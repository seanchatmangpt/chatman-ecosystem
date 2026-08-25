from .refusal import Refused
def require_worst_loss_monotone(points):
    rows=sorted(points,key=lambda p:p[0])
    for (_,a),(_,b) in zip(rows,rows[1:]):
        if b<a: raise Refused("REFUSED[NON_MONOTONE_WORST_CASE_LOSS]")
    return True
