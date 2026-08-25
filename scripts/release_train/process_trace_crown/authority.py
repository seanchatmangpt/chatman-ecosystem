from __future__ import annotations
from enum import Enum
from .refusal import Refused

class ActionClass(str, Enum):
    OBSERVE="OBSERVE"; SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"

def admit(action: ActionClass, broker: str | None = None) -> None:
    if action is ActionClass.DO and broker != "BRCE":
        raise Refused("BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO")
