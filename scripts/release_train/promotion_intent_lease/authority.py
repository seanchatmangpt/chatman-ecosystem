from enum import Enum
from .subject import Refusal
class ActionClass(str, Enum):
    OBSERVE='OBSERVE'; SELECT='SELECT'; CONSTRUCT='CONSTRUCT'; VERIFY='VERIFY'; DO='DO'; MERGE='MERGE'; RELEASE='RELEASE'; DEPLOY='DEPLOY'; LIVE_CLOUD='LIVE_CLOUD'

def require(action: ActionClass) -> None:
    if action in {ActionClass.DO,ActionClass.MERGE,ActionClass.RELEASE,ActionClass.DEPLOY,ActionClass.LIVE_CLOUD}:
        raise Refusal('REFUSED[BRCE_REQUIRED]')
