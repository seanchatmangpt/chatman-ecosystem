def correlated_clusters(witnesses, independence, provenance):
    n=len(witnesses); parent=list(range(n))
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b: parent[b]=a
    for i in range(n):
        for j in range(i+1,n):
            if independence.relation(witnesses[i],witnesses[j],provenance) in {"SAME_EVIDENCE","CORRELATED"}: union(i,j)
    groups={}
    for i,w in enumerate(witnesses): groups.setdefault(find(i),[]).append(w)
    return tuple(tuple(sorted(g,key=lambda x:x.evidence_id)) for g in sorted(groups.values(),key=lambda g:min(x.evidence_id for x in g)))
