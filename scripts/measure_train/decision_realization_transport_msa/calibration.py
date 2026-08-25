from fractions import Fraction
def calibration_gap(observations):
    rows=tuple(observations)
    if not rows:return Fraction(0)
    return sum((abs(o.predicted_risk-o.realized_loss) for o in rows),Fraction(0))/len(rows)
def transport_calibration_gap(source,target):
    return abs(calibration_gap(source)-calibration_gap(target))
