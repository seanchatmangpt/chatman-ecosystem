from dataclasses import dataclass

@dataclass(frozen=True)
class DriftResult:
    alarm: bool
    statistic: float
    first_alarm_index: int | None

def cusum(values, target, threshold):
    s=0.0
    for i,value in enumerate(values):
        s=max(0.0,s+(value-target))
        if s>threshold:
            return DriftResult(True,s,i)
    return DriftResult(False,s,None)
