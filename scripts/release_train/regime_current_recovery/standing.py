from dataclasses import dataclass

@dataclass(frozen=True)
class QualificationStanding:
    standing: str
    reason: str

def bounded_standing(outcomes: list[str], decision: str, independent_clusters: int, blockers: tuple, current_regime: bool) -> QualificationStanding:
    if blockers: return QualificationStanding('BLOCKED','DEPENDENCY_BLOCKER')
    if 'FAIL' in outcomes or decision=='REJECT': return QualificationStanding('BUILD_BROKEN','EXPLICIT_FAILURE')
    if not current_regime: return QualificationStanding('UNKNOWN','STALE_OR_DRIFTED_CALIBRATION')
    if independent_clusters<2: return QualificationStanding('UNKNOWN','INSUFFICIENT_INDEPENDENT_CLUSTERS')
    if decision=='ACCEPT_BOUNDED': return QualificationStanding('PARTIAL_ALIVE','CURRENT_CALIBRATED_INDEPENDENT_EVIDENCE')
    return QualificationStanding('UNKNOWN','INSUFFICIENT_INFORMATION')
