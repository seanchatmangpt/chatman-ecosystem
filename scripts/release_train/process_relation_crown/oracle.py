from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class OracleWitness:
    implementation_digest:str; model_digest:str; verdict_digest:str
def require_independent(a:OracleWitness,b:OracleWitness):
    if a.implementation_digest==b.implementation_digest: raise Refused("ORACLE_IMPLEMENTATION_COLLUSION")
    if a.model_digest==b.model_digest: raise Refused("ORACLE_MODEL_COLLUSION")
    if a.verdict_digest!=b.verdict_digest: raise Refused("ORACLE_DISAGREEMENT")
    return True
