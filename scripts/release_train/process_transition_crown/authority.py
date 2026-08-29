from dataclasses import dataclass
from enum import Enum
from .refusal import Refused

class ActionClass(str, Enum):
    OBSERVE="OBSERVE"; SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"

@dataclass(frozen=True)
class AuthorityProof:
    broker: str|None=None
    receipt_digest: str|None=None
    postcondition: str|None=None


def admit_action(action: ActionClass, proof: AuthorityProof|None=None) -> ActionClass:
    if action != ActionClass.DO:
        return action
    if not proof or proof.broker != "BRCE" or not proof.receipt_digest or not proof.postcondition:
        raise Refused("BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO")
    return action
