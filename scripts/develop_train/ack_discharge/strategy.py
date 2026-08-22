from dataclasses import dataclass
from enum import StrEnum
class Strategy(StrEnum): ALL='ALL'; QUORUM='QUORUM'; CRITICAL_PATH='CRITICAL_PATH'
@dataclass(frozen=True,slots=True)
class FrontierItem: identity:str; discharged:bool; critical:bool
def is_complete(strategy,items):
 if not items:return True
 if strategy is Strategy.ALL:return all(i.discharged for i in items)
 if strategy is Strategy.QUORUM:return sum(i.discharged for i in items)>=len(items)//2+1
 critical=[i for i in items if i.critical];return bool(critical) and all(i.discharged for i in critical)
