from fractions import Fraction
from .refusal import Refused

class Cusum:
    def __init__(self, reference=Fraction(1, 10), threshold=Fraction(1)):
        if reference < 0 or threshold <= 0:
            raise Refused("INVALID_CUSUM")
        self.reference = reference
        self.threshold = threshold

    def run(self, losses):
        cumulative = Fraction(0)
        peak = Fraction(0)
        for loss in losses:
            cumulative = max(Fraction(0), cumulative + Fraction(loss) - self.reference)
            peak = max(peak, cumulative)
        return {"peak": peak, "drifted": peak >= self.threshold}
