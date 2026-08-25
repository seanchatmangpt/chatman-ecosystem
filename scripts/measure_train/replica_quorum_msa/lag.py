from statistics import median
def lag_profile(observations, now):
    lags=tuple(sorted((now-o.observed_at).total_seconds() for o in observations))
    if any(x<0 for x in lags): raise ValueError("REFUSED[FUTURE_OBSERVATION]")
    if not lags:return {"count":0,"median":None,"max":None}
    return {"count":len(lags),"median":median(lags),"max":max(lags)}
