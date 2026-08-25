from dataclasses import dataclass
from .refusal import require

@dataclass(frozen=True)
class Calibration:
    generation: int
    support: int
    miss_rate: float
    mean_width: float
    digest: str

    def __post_init__(self) -> None:
        require(self.generation >= 0, "INVALID_GENERATION")
        require(self.support > 0, "INSUFFICIENT_CALIBRATION_SUPPORT")
        require(0 <= self.miss_rate <= 1, "INVALID_MISS_RATE")
        require(self.mean_width >= 0, "INVALID_MEAN_WIDTH")
        require(len(self.digest)==64 and all(c in '0123456789abcdef' for c in self.digest), "INVALID_CALIBRATION_DIGEST")


def current_calibration(items: tuple[Calibration,...], expected_generation: int, max_miss: float) -> Calibration:
    current=[x for x in items if x.generation==expected_generation]
    require(len(current)==1, "DIVERGENT_CURRENT_CALIBRATION" if len(current)>1 else "STALE_CALIBRATION")
    c=current[0]; require(c.miss_rate <= max_miss, "CALIBRATION_MISS_EXCEEDED")
    return c


def cusum(values: tuple[float,...], target: float, allowance: float, threshold: float) -> bool:
    s=0.0
    for value in values:
        s=max(0.0,s+(value-target)-allowance)
        if s >= threshold: return True
    return False
