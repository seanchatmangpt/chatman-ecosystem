def jaccard_overlap(a,b):
    x,y=set(a),set(b)
    if not x and not y: return 0.0
    return len(x&y)/len(x|y)
def overlap_matrix(outcomes):
    rows=[]
    for i,a in enumerate(outcomes):
        for b in outcomes[i+1:]: rows.append((a.sensor_id,b.sensor_id,jaccard_overlap(a.case_ids,b.case_ids)))
    return tuple(sorted(rows))
