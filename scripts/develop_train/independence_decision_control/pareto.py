def pareto(candidates):
    def dominates(left, right):
        weak = left.expected_loss <= right.expected_loss and left.false_independent <= right.false_independent and left.information_value >= right.information_value and left.drift_risk <= right.drift_risk
        strict = left.expected_loss < right.expected_loss or left.false_independent < right.false_independent or left.information_value > right.information_value or left.drift_risk < right.drift_risk
        return weak and strict

    return tuple(item for item in candidates if not any(dominates(other, item) for other in candidates if other is not item))
