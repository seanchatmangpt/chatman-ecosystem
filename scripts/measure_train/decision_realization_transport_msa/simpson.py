from fractions import Fraction
def mean_loss(rows):
    rows=tuple(rows)
    return sum((o.realized_loss for o in rows),Fraction(0))/len(rows) if rows else Fraction(0)
def simpson_reversal(source,target):
    raw=mean_loss(source)-mean_loss(target)
    common=set(o.stratum for o in source)&set(o.stratum for o in target)
    directions=[]
    for s in common:
        directions.append(mean_loss([o for o in source if o.stratum==s])-mean_loss([o for o in target if o.stratum==s]))
    return bool(directions and raw!=0 and all(d!=0 and (d>0)!=(raw>0) for d in directions))
