from .subject import Subject, Refused

def normalize_observation(repo, sha, generation, event_id, state, source):
    subject=Subject(repo,sha)
    if generation < 0: raise Refused("REFUSED[INVALID_GENERATION]")
    if state not in {"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}: raise Refused("REFUSED[INVALID_OBSERVATION_STATE]")
    if not source.strip(): raise Refused("REFUSED[EMPTY_OBSERVATION_SOURCE]")
    return {"subject":subject,"generation":generation,"event_id":event_id,"state":state,"source":source}

def reconcile_observations(rows):
    grouped={}
    for row in rows:
        key=(row["subject"],row["generation"],row["event_id"])
        grouped.setdefault(key,set()).add(row["state"])
    return tuple(sorted((k[0].repo,k[0].sha,k[1],k[2],tuple(sorted(v))) for k,v in grouped.items()))
