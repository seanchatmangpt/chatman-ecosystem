from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class EngineWitness:
    engine: str; implementation: str; model: str; semantic: str; trace: str; obligation: str

def require_engines(witnesses):
    ws=tuple(witnesses)
    if len(ws)<2: raise Refused("INSUFFICIENT_ENGINE_CORRESPONDENCE")
    if len({(w.implementation,w.model) for w in ws})<2: raise Refused("ENGINE_COLLUSION")
    if len({(w.semantic,w.trace,w.obligation) for w in ws})!=1: raise Refused("ENGINE_DIVERGENCE")
    return True

@dataclass(frozen=True)
class RegionWitness:
    host: str; region: str; encrypted: bool; certificate: str; generation: int

def require_regions(witnesses,generation):
    ws=tuple(witnesses)
    if len({w.host for w in ws})<2 or len({w.region for w in ws})<2: raise Refused("INSUFFICIENT_REGION_DIVERSITY")
    if any(not w.encrypted or not w.certificate or w.generation!=generation for w in ws): raise Refused("TLS_CURRENTNESS_CONTRADICTION")
    return True
