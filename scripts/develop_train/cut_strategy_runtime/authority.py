from __future__ import annotations
from enum import Enum
from .identity import Refusal
class ActionClass(str, Enum):
    OBSERVE="OBSERVE"; SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"
def require_nonconsequential(action: ActionClass) -> None:
    if action is ActionClass.DO: raise Refusal("REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]")
