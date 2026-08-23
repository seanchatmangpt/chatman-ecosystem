from fractions import Fraction
from .subject import Refused
from .loss import realized_loss
def weights(source,target,max_weight=Fraction(20)):
    s,t=source.as_dict(),target.as_dict(); out={}
    for k,tv in t.items():
        sv=s.get(k,Fraction(0))
        if tv>0 and sv<=0: raise Refused("REFUSED[POSITIVITY_VIOLATION]")
        w=tv/sv if sv else Fraction(0)
        if w>max_weight: raise Refused("REFUSED[TRANSPORT_WEIGHT_CONCENTRATION]")
        out[k]=w
    return out
def effective_sample(observations,cell_fn,weight_map):
    ws=[weight_map.get(cell_fn(o),Fraction(0))/o.propensity for o in observations if o.labeled]
    if not ws: return Fraction(0)
    s=sum(ws,Fraction(0)); sq=sum((x*x for x in ws),Fraction(0))
    return s*s/sq if sq else Fraction(0)
def transported_risk(observations,matrix,cell_fn,weight_map):
    rows=[o for o in observations if o.labeled]
    if not rows: raise Refused("REFUSED[EMPTY_TRANSPORT_SAMPLE]")
    ws=[weight_map.get(cell_fn(o),Fraction(0))/o.propensity for o in rows]
    den=sum(ws,Fraction(0))
    if den<=0: raise Refused("REFUSED[ZERO_TRANSPORT_MASS]")
    return sum((w*realized_loss(o,matrix) for w,o in zip(ws,rows)),Fraction(0))/den
