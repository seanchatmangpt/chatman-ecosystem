from dataclasses import dataclass
@dataclass(frozen=True)
class TransitionMetrics:
    attempts:int; commits:int; refusals:int; io_failures:int; contention_rate:float; commit_yield:float
def measure(transitions):
    n=len(transitions); commits=sum(t.outcome=="COMMITTED" for t in transitions); refusals=sum(t.outcome in {"CAS_REFUSED","CORRUPTION_REFUSED"} for t in transitions); failures=sum(t.outcome=="IO_FAILURE" for t in transitions)
    return TransitionMetrics(n,commits,refusals,failures,refusals/n if n else 0.0,commits/n if n else 0.0)
