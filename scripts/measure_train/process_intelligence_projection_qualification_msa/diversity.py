from fractions import Fraction
def diversity(projections):
    rows=tuple(projections)
    if not rows:return {"engine":Fraction(0),"runtime":Fraction(0),"root":Fraction(0)}
    n=len(rows); return {"engine":Fraction(len({p.engine for p in rows}),n),"runtime":Fraction(len({p.runtime for p in rows}),n),"root":Fraction(len({p.evidence_root for p in rows}),n)}
