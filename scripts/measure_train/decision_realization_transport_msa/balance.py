def stratum_balance(source_dist,target_dist):
    keys=set(source_dist)|set(target_dist)
    gaps={k:abs(float(source_dist.get(k,0))-float(target_dist.get(k,0))) for k in keys}
    return {"max_gap":max(gaps.values(),default=0.0),"gaps":gaps}
