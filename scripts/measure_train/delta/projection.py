def to_ocel_event(repo,subject_sha,activity,timestamp,outcome,attrs=None):
    return {"ocel:activity":activity,"ocel:timestamp":timestamp.isoformat(),"ocel:objects":[{"type":"repository-subject","id":f"{repo}@{subject_sha}"}],"ocel:vmap":{"outcome":outcome,**(attrs or {})}}
