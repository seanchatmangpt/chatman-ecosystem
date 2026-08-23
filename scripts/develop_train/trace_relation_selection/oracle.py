from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True)
class OracleWitness:
    implementation_digest: str
    model_digest: str

def require_independent(oracles) -> None:
    impls = [o.implementation_digest for o in oracles]
    models = [o.model_digest for o in oracles]
    if len(oracles) < 2:
        raise Refused("REFUSED[INSUFFICIENT_ORACLES]")
    if len(set(impls)) != len(impls) or len(set(models)) != len(models):
        raise Refused("REFUSED[ORACLE_ALIASING]")
