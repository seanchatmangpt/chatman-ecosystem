from dataclasses import dataclass
from .subject import Refusal

@dataclass(frozen=True)
class CusumResult:
    positive: float
    negative: float
    alarm: bool

def detect_error_shift(errors: list[int], reference: float=0.2, slack: float=0.05, threshold: float=1.5) -> CusumResult:
    if not errors or any(e not in (0,1) for e in errors): raise Refusal('REFUSED[INVALID_ERROR_SEQUENCE]')
    if not (0 <= reference <= 1) or slack < 0 or threshold <= 0: raise Refusal('REFUSED[INVALID_CUSUM_PARAMETERS]')
    positive=negative=0.0
    for error in errors:
        delta=error-reference
        positive=max(0.0,positive+delta-slack)
        negative=min(0.0,negative+delta+slack)
    return CusumResult(round(positive,12),round(negative,12),positive>=threshold or abs(negative)>=threshold)
