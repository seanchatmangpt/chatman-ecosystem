from collections import defaultdict
def worst_stratum(rows,key):
    g=defaultdict(list)
    for r in rows:g[key(r)].append(r)
    if not g:return None
    return max(((name,sum(abs(x.certificate.primal-x.realized_cost) for x in rs)/len(rs)) for name,rs in g.items()),key=lambda x:x[1])
