from .refusal import Refused
def current_models(models):
    by={}
    for m in models:
        key=(m.kind,m.ground_metric_digest); old=by.get(key)
        if old is None or m.generation>old.generation: by[key]=m
        elif m.generation==old.generation and m.digest!=old.digest: raise Refused("REFUSED[DIVERGENT_CURRENT_AMBIGUITY_MODEL]")
    return tuple(sorted(by.values(),key=lambda m:(m.kind,m.ground_metric_digest or '',m.digest)))
