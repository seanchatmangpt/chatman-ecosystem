from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from .identity import Subject
from .methodology import Methodology, MethodologySet
from .projection import Projection, correspondence
from .receipt import Receipt
from .authority import ActionClass, admit_action

@dataclass(frozen=True)
class Qualification:
    standing: str
    missing: tuple[str, ...]
    receipt: Receipt | None

REQUIRED = frozenset(Methodology)


def qualify(subject: Subject, methodologies: MethodologySet, projections: tuple[Projection, ...], rails: tuple[str, ...], action: ActionClass = ActionClass.VERIFY) -> Qualification:
    admit_action(action)
    missing = tuple(sorted(m.value for m in methodologies.missing(REQUIRED)))
    if missing:
        return Qualification("UNKNOWN", missing, None)
    for left, right in zip(projections, projections[1:]):
        correspondence(left, right)
    semantic = projections[0].semantic_digest if projections else sha256(subject.canonical().encode()).hexdigest()
    receipt = Receipt(subject.canonical(), semantic, "PARTIAL_ALIVE", tuple(sorted(set(rails))))
    return Qualification("PARTIAL_ALIVE", (), receipt)
