from enum import Enum
from dataclasses import dataclass

class Obligation(str, Enum):
    METHODOLOGY_COVERAGE="METHODOLOGY_COVERAGE"
    POWL_SOUNDNESS="POWL_SOUNDNESS"
    POWL_COMPLETENESS="POWL_COMPLETENESS"
    REACTOR_CANONICAL="REACTOR_CANONICAL"
    MULTI_ENGINE_EQUIVALENCE="MULTI_ENGINE_EQUIVALENCE"
    INDEPENDENT_ORACLE="INDEPENDENT_ORACLE"
    MULTI_REGION_TLS="MULTI_REGION_TLS"
    FAILURE_COURTS="FAILURE_COURTS"
    BRCE_ONLY_DO="BRCE_ONLY_DO"
    RECEIPT_DAG="RECEIPT_DAG"
    GLOBAL_REPLAY="GLOBAL_REPLAY"
    EXACT_HEAD="EXACT_HEAD"

REQUIRED=frozenset(Obligation)

@dataclass(frozen=True)
class ClosureCensus:
    satisfied: frozenset[Obligation]
    failed: frozenset[Obligation] = frozenset()

    @property
    def missing(self):
        return tuple(sorted((x.value for x in REQUIRED-self.satisfied-self.failed)))

    @property
    def failures(self):
        return tuple(sorted(x.value for x in self.failed))
