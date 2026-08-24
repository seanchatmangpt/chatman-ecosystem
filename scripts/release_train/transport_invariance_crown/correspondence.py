from dataclasses import dataclass
from .refusal import require

@dataclass(frozen=True)
class EngineEvidence:
    engine: str
    implementation: str
    model_family: str
    semantic_digest: str
    trace_digest: str
    obligation_digest: str

@dataclass(frozen=True)
class OracleEvidence:
    kind: str
    implementation: str
    model_family: str
    digest: str

@dataclass(frozen=True)
class RegionEvidence:
    host: str
    region: str
    certificate_digest: str
    encrypted: bool
    generation: int


def admit_correspondence(engines: tuple[EngineEvidence,...],oracles: tuple[OracleEvidence,...],regions: tuple[RegionEvidence,...],generation:int) -> None:
    require(len(engines)>=2,"INSUFFICIENT_ENGINE_EVIDENCE")
    require(len({e.implementation for e in engines})>=2 and len({e.model_family for e in engines})>=2,"NONINDEPENDENT_ENGINE_EVIDENCE")
    triples={(e.semantic_digest,e.trace_digest,e.obligation_digest) for e in engines}
    require(len(triples)==1,"ENGINE_CORRESPONDENCE_DIVERGENCE")
    kinds={o.kind for o in oracles}; require({'POWL','OCEL'}<=kinds,"MISSING_INDEPENDENT_ORACLE")
    require(len({(o.implementation,o.model_family) for o in oracles})>=2,"NONINDEPENDENT_ORACLE_EVIDENCE")
    current=[r for r in regions if r.generation==generation and r.encrypted and len(r.certificate_digest)==64]
    require(len({r.host for r in current})>=2 and len({r.region for r in current})>=2,"INSUFFICIENT_MULTI_REGION_TLS")
