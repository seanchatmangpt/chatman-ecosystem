from fractions import Fraction
from .errors import Refused
def inverse(m):
    n=len(m)
    if not n or any(len(r)!=n for r in m): raise Refused("NON_SQUARE_MATRIX")
    a=[[Fraction(x) for x in row]+[Fraction(int(i==j)) for j in range(n)] for i,row in enumerate(m)]
    for c in range(n):
        p=next((r for r in range(c,n) if a[r][c]),None)
        if p is None: raise Refused("SINGULAR_CORRELATION_GEOMETRY")
        a[c],a[p]=a[p],a[c]; s=a[c][c]; a[c]=[x/s for x in a[c]]
        for r in range(n):
            if r==c: continue
            f=a[r][c]
            if f: a[r]=[x-f*y for x,y in zip(a[r],a[c])]
    return [r[n:] for r in a]
