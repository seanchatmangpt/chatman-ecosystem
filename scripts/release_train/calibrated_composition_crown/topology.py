from .refusal import Refused
METHODS=frozenset({"discovery","conformance","simulation","prediction","optimization","intervention","monitoring","event_centric","object_centric","declarative","procedural"})
RAILS=frozenset({"SEMANTIC","POWL","REACTOR","BEAM","PLAN","WASM","NIF","REMOTE","BRCE"})
FAILURES=frozenset({"node","partition","latency","loss","version","certificate","ambiguous_do"})
def require_complete(observed, required, code):
    missing=required-set(observed)
    if missing: raise Refused(code)
    return True
