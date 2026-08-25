def worst_stratum(observations):
    grouped={}
    for o in observations: grouped.setdefault((o.projection.methodology,o.projection.engine,o.projection.runtime),[]).append(o)
    ranked=[]
    for key,rows in grouped.items(): ranked.append((sum(1 for x in rows if x.state in {"FAIL","REFUSED"})/len(rows),key,len(rows)))
    return max(ranked,default=(0.0,None,0))
