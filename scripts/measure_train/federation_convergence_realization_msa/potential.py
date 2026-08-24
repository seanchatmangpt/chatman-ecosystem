from fractions import Fraction
def value(o): return Fraction(5)*o.blocker_count+Fraction(3)*o.error_mass+o.churn_mass
def deltas(rows):
    v=[value(r) for r in rows]; return tuple(b-a for a,b in zip(v,v[1:]))
def descent_fraction(rows):
    ds=deltas(rows); return Fraction(0) if not ds else Fraction(sum(d<0 for d in ds),len(ds))
