from dataclasses import dataclass
from .refusals import Refused

@dataclass(frozen=True)
class SensorDescriptor:
    sensor_id: str
    family: str
    domain: str

@dataclass(frozen=True)
class IndependenceProof:
    pairs: frozenset[tuple[str, str]]

    def admits(self, left: SensorDescriptor, right: SensorDescriptor) -> bool:
        if left.sensor_id == right.sensor_id:
            return False
        if left.family == right.family or left.domain == right.domain:
            return False
        pair = tuple(sorted((left.sensor_id, right.sensor_id)))
        return pair in self.pairs

def require_independent(left: SensorDescriptor, right: SensorDescriptor, proof: IndependenceProof) -> None:
    if not proof.admits(left, right):
        raise Refused("REFUSED_UNPROVEN_SENSOR_INDEPENDENCE")
