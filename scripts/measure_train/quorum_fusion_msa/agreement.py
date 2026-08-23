from collections import defaultdict
def pairwise_agreement(trials):
    by_case=defaultdict(dict)
    for t in trials: by_case[t.case_id][t.sensor.sensor_id]=t.prediction
    counts={}
    ids=sorted({t.sensor.sensor_id for t in trials})
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            same=total=0
            for row in by_case.values():
                if a in row and b in row:
                    total+=1; same+=row[a]==row[b]
            counts[(a,b)] = (same/total if total else None)
    return counts
