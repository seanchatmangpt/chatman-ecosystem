from .independence import relation

def correlated_clusters(observations, edges=()):
    rows=list(observations)
    parent=list(range(len(rows)))
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b: parent[b]=a
    for i in range(len(rows)):
        for j in range(i+1,len(rows)):
            if relation(rows[i],rows[j],edges)=="CORRELATED":
                union(i,j)
    groups={}
    for i,row in enumerate(rows):
        groups.setdefault(find(i),[]).append(row)
    return tuple(tuple(sorted(group)) for group in sorted(groups.values(), key=lambda g:min(x.evidence_id for x in g)))
