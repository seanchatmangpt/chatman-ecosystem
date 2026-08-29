from fractions import Fraction
from .refusal import refuse
from .support import weights

def ips(rows):
    ws=weights(rows); return sum((w*r.reward for w,r in zip(ws,rows)),Fraction(0))/len(rows)

def snips(rows):
    ws=weights(rows); den=sum(ws,Fraction(0))
    if den<=0: refuse("ZERO_TARGET_MASS")
    return sum((w*r.reward for w,r in zip(ws,rows)),Fraction(0))/den

def doubly_robust(rows):
    if any(r.model_prediction is None for r in rows): refuse("MODEL_PROVENANCE_REQUIRED")
    ws=weights(rows)
    return sum((r.model_prediction+w*(r.reward-r.model_prediction) for w,r in zip(ws,rows)),Fraction(0))/len(rows)
