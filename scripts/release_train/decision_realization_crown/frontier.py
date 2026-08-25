from .errors import Refused
def current(models):
    models=tuple(models)
    if not models: raise Refused("NO_REALIZATION_MODEL")
    g=max(m.generation for m in models); latest=[m for m in models if m.generation==g]
    if len({m.digest for m in latest})!=1: raise Refused("DIVERGENT_REALIZATION_FRONTIER")
    return latest[0]
