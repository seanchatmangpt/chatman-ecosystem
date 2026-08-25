from dataclasses import dataclass

@dataclass(frozen=True)
class Cusum:
    value: float = 0.0
    threshold: float = 1.0
    slack: float = 0.0

    def update(self, residual: float):
        nxt = max(0.0, self.value + abs(float(residual)) - self.slack)
        return Cusum(nxt, self.threshold, self.slack)

    @property
    def changed(self):
        return self.value >= self.threshold
