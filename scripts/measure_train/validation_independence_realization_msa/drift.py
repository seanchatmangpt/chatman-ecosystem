from dataclasses import dataclass
@dataclass(frozen=True)
class Drift:
    score:float; alarm:bool
def cusum_false_independence(sequence,target=0.05,slack=0.01,threshold=0.5):
    s=0.0
    for value in sequence:
        x=1.0 if value else 0.0
        s=max(0.0,s+x-target-slack)
    return Drift(s,s>=threshold)
