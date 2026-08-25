from .interval import frechet_and, independent_and
from .subject import Refused
def compose(a,b,mode,witness=None):
    if mode=="UNKNOWN_DEPENDENCE":
        return frechet_and(a,b)
    if mode=="INDEPENDENT":
        if witness is None: raise Refused("REFUSED[MISSING_INDEPENDENCE_WITNESS]")
        witness.admit()
        return independent_and(a,b)
    raise Refused("REFUSED[UNKNOWN_COMPOSITION_MODE]")
