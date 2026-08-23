import math
def entropy(values):
    vals=tuple(values); n=len(vals)
    if not n:return 0.0
    counts={}
    for v in vals: counts[v]=counts.get(v,0)+1
    return -sum((c/n)*math.log2(c/n) for c in counts.values())
def total_correlation(rows):
    rows=tuple(tuple(int(bool(x)) for x in row) for row in rows)
    if not rows:return 0.0
    width=len(rows[0])
    if any(len(r)!=width for r in rows): raise ValueError("ragged rows")
    return max(0.0,sum(entropy(r[i] for r in rows) for i in range(width))-entropy(rows))
def higher_order_excess(rows):
    rows=tuple(rows)
    if not rows or len(rows[0])<3:return 0.0
    total=total_correlation(rows); pair_max=0.0
    for i in range(len(rows[0])):
        for j in range(i+1,len(rows[0])): pair_max=max(pair_max,total_correlation([(r[i],r[j]) for r in rows]))
    return max(0.0,total-pair_max)
