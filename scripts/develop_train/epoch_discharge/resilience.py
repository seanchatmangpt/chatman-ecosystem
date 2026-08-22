from __future__ import annotations
from dataclasses import dataclass
import random

@dataclass(frozen=True, slots=True)
class RetryDecision:
    attempt:int; succeeded:bool

def deterministic_retry(seed:int, failure_probability:float, max_attempts:int)->tuple[RetryDecision,...]:
    if not 0<=failure_probability<=1: raise ValueError("REFUSED[INVALID_FAILURE_PROBABILITY]")
    if max_attempts<1: raise ValueError("REFUSED[INVALID_RETRY_BUDGET]")
    rng=random.Random(seed); out=[]
    for attempt in range(1,max_attempts+1):
        ok=rng.random() >= failure_probability
        out.append(RetryDecision(attempt,ok))
        if ok: break
    return tuple(out)
