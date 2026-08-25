from dataclasses import dataclass

from .errors import Refused


@dataclass(frozen=True)
class OracleWitness:
    kind: str
    implementation: str
    model: str
    digest: str


def require_oracles(witnesses, kind):
    selected = [witness for witness in witnesses if witness.kind == kind]
    if len({(witness.implementation, witness.model) for witness in selected}) < 2:
        raise Refused("ORACLE_ALIAS")
    if len({witness.digest for witness in selected}) != 1:
        raise Refused("ORACLE_DIVERGENCE")
    return True
