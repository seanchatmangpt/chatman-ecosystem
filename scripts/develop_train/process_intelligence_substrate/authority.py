from __future__ import annotations
from enum import Enum
from .errors import Refused

class ActionClass(str, Enum):
    OBSERVE="OBSERVE"; SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"


def admit_action(action: ActionClass) -> None:
    if action is ActionClass.DO:
        raise Refused("BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO")
