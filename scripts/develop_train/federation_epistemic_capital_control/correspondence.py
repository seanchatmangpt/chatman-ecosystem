from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class EngineWitness: engine:str; implementation:str; semantic_digest:str; trace_digest:str; obligation_digest:str
@dataclass(frozen=True)
class RegionWitness: host:str; region:str; generation:int; semantic_digest:str; encrypted:bool; certificate_digest:str
def require_engines(ws):
    ws=tuple(ws)
    if len({w.engine for w in ws})<2 or len({w.implementation for w in ws})<2: raise Refused('INSUFFICIENT_ENGINE_INDEPENDENCE')
    if len({(w.semantic_digest,w.trace_digest,w.obligation_digest) for w in ws})!=1: raise Refused('ENGINE_CORRESPONDENCE_DIVERGENCE')
    return True
def require_regions(ws):
    ws=tuple(ws)
    if len({w.host for w in ws})<2 or len({w.region for w in ws})<2: raise Refused('INSUFFICIENT_REGION_DIVERSITY')
    if not all(w.encrypted and w.certificate_digest for w in ws): raise Refused('TLS_FACT_CORRESPONDENCE_FAILURE')
    if len({(w.generation,w.semantic_digest) for w in ws})!=1: raise Refused('REGION_CURRENTNESS_DIVERGENCE')
    return True
