from .refusal import Refused
def matrix(ids,assoc):
    ids=tuple(sorted(ids)); idx={x:i for i,x in enumerate(ids)}; n=len(ids); m=[[0.0]*n for _ in range(n)]
    for i in range(n): m[i][i]=1.0
    for a in assoc:
        i,j=idx[a.left],idx[a.right]; m[i][j]=m[j][i]=a.phi
    return tuple(tuple(r) for r in m)
def require_bounds(m):
    n=len(m)
    if any(len(r)!=n for r in m): raise Refused("REFUSED[NON_SQUARE_MATRIX]")
    if any(abs(m[i][i]-1)>1e-9 for i in range(n)): raise Refused("REFUSED[INVALID_DIAGONAL]")
    if any(abs(m[i][j]-m[j][i])>1e-9 or abs(m[i][j])>1+1e-9 for i in range(n) for j in range(n)): raise Refused("REFUSED[INVALID_CORRELATION]")
    return True
