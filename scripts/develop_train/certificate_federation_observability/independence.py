from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class Independence: transports:tuple[str,...]; implementations:tuple[str,...]; models:tuple[str,...]; domains:tuple[str,...]
def witness(transports):
    ts=tuple(transports)
    if len(ts)<2: raise Refused("INSUFFICIENT_INDEPENDENT_TRANSPORTS")
    if len({t.transport_id for t in ts})!=len(ts): raise Refused("TRANSPORT_ALIAS")
    for attr,code in (("implementation","SHARED_IMPLEMENTATION"),("model","SHARED_MODEL"),("domain","SHARED_DOMAIN")):
        vals=[getattr(t,attr) for t in ts]
        if len(set(vals))!=len(vals): raise Refused(code)
    return Independence(tuple(t.transport_id for t in ts),tuple(t.implementation for t in ts),tuple(t.model for t in ts),tuple(t.domain for t in ts))
