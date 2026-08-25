from fractions import Fraction
def effective_capital(projections):
    rows=tuple(projections)
    if not rows:return Fraction(0)
    unique={(p.engine,p.runtime,p.evidence_root,p.result_digest) for p in rows}
    return Fraction(len(unique),len(rows))
