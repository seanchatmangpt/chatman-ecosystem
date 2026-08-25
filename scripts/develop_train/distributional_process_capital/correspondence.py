from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class EngineWitness:
    engine:str
    implementation:str
    model:str
    semantic:str
    trace:str
    obligations:str
@dataclass(frozen=True)
class RegionWitness:
    host:str
    region:str
    encrypted:bool
    certificate:str
    generation:int

def require_engines(witnesses):
    ws=tuple(witnesses)
    if len({w.engine for w in ws})<2 or len({w.implementation for w in ws})<2 or len({w.model for w in ws})<2:
        raise Refused("INSUFFICIENT_ENGINE_INDEPENDENCE")
    if len({(w.semantic,w.trace,w.obligations) for w in ws})!=1:
        raise Refused("ENGINE_CORRESPONDENCE_DIVERGENCE")
    return True

def require_regions(witnesses):
    ws=tuple(witnesses)
    if len({w.host for w in ws})<2 or len({w.region for w in ws})<2:
        raise Refused("INSUFFICIENT_REGION_DIVERSITY")
    if not all(w.encrypted and w.certificate for w in ws):
        raise Refused("TLS_EVIDENCE_INVALID")
    if len({w.generation for w in ws})!=1:
        raise Refused("STALE_REGION_GENERATION")
    return True
