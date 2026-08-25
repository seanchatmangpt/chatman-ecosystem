from .refusal import Refused

def require_current(model,frontier):
    current={m.estimator_id:m for m in frontier}.get(model.estimator_id)
    if current is None: raise Refused("REFUSED[UNKNOWN_ESTIMATOR_MODEL]")
    if current.generation!=model.generation or current.digest!=model.digest: raise Refused("REFUSED[STALE_ESTIMATOR_MODEL]")
    return "CURRENT"
