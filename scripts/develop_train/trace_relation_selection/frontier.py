from dataclasses import dataclass
from .relation import Relation
from .calibration import CalibrationEvidence
from .refusal import Refused

@dataclass(frozen=True)
class CalibrationFrontier:
    generation: int
    evidence: tuple[CalibrationEvidence, ...]

    @classmethod
    def current(cls, evidence) -> "CalibrationFrontier":
        items = tuple(evidence)
        if not items:
            raise Refused("REFUSED[EMPTY_CALIBRATION_FRONTIER]")
        latest = max(e.generation for e in items)
        current = tuple(e for e in items if e.generation == latest)
        by_relation = {}
        for e in current:
            if e.relation in by_relation and by_relation[e.relation] != e:
                raise Refused("REFUSED[SPLIT_CALIBRATION_FRONTIER]")
            by_relation[e.relation] = e
        return cls(latest, tuple(sorted(by_relation.values(), key=lambda e: e.relation.value)))

    def get(self, relation: Relation) -> CalibrationEvidence:
        for e in self.evidence:
            if e.relation == relation:
                return e
        raise Refused("REFUSED[MISSING_RELATION_CALIBRATION]")
