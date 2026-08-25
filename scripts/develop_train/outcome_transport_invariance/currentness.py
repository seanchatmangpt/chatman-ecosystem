from dataclasses import dataclass

@dataclass(frozen=True)
class Cusum:
    score: float = 0
    threshold: float = 1
    slack: float = 0

    def update(self, residual):
        return Cusum(max(0, self.score + abs(float(residual)) - self.slack), self.threshold, self.slack)

    @property
    def changed(self):
        return self.score >= self.threshold

def stable(calibration, cusum):
    return calibration.admitted() and not cusum.changed
