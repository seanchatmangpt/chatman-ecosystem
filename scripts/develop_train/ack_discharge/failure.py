from dataclasses import dataclass
import random
@dataclass(frozen=True,slots=True)
class FailurePlan:
 seed:int; failure_probability:float; attempts:int=3
 def __post_init__(self):
  if not 0<=self.failure_probability<=1:raise ValueError('REFUSED[INVALID_FAILURE_PROBABILITY]')
  if self.attempts<1:raise ValueError('REFUSED[INVALID_RETRY_BUDGET]')
def simulate_delivery(identities,plan):
 rng=random.Random(plan.seed);out={}
 for identity in sorted(identities):
  success=None
  for attempt in range(1,plan.attempts+1):
   if rng.random()>=plan.failure_probability:success=attempt;break
  out[identity]=success
 return out
