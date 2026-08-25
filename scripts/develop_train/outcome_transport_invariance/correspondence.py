from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class Engine:
    engine: str
    implementation: str
    model: str
    semantic: str
    trace: str
    obligation: str

@dataclass(frozen=True)
class Region:
    host: str
    region: str
    certificate: str
    encrypted: bool
    current: bool

def engines(values):
    values = tuple(values)
    if min(len({x.engine for x in values}), len({x.implementation for x in values}), len({x.model for x in values})) < 2:
        raise Refused("PSEUDO_ENGINE_INDEPENDENCE")
    if len({(x.semantic, x.trace, x.obligation) for x in values}) != 1:
        raise Refused("ENGINE_DIVERGENCE")
    return True

def regions(values):
    values = tuple(values)
    if len({x.host for x in values}) < 2 or len({x.region for x in values}) < 2:
        raise Refused("INSUFFICIENT_REGIONS")
    if any(not x.current or not x.encrypted or not x.certificate for x in values):
        raise Refused("INVALID_TLS_REGION")
    return True
