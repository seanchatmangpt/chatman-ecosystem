from dataclasses import dataclass
from .relation import Relation

@dataclass(frozen=True)
class SelectionBundle:
    strongest: tuple[Relation, ...]
    minimax: Relation | None
    pareto: tuple[Relation, ...]
    information: Relation | None

    @property
    def disagree(self) -> bool:
        identities = set(self.strongest)
        if self.minimax is not None:
            identities.add(self.minimax)
        if self.information is not None:
            identities.add(self.information)
        identities.update(self.pareto)
        return len(identities) > 1
