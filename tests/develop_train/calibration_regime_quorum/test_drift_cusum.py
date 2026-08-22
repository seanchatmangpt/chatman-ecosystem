import unittest
from datetime import datetime,timedelta,timezone
from fractions import Fraction
from scripts.develop_train.calibration_regime_quorum.calibration import fit_model
from scripts.develop_train.calibration_regime_quorum.cusum import prequential_cusum
from scripts.develop_train.calibration_regime_quorum.drift import classify_drift,compare_models
from scripts.develop_train.calibration_regime_quorum.trials import CalibrationTrial
def model(source,pairs):
    now=datetime.now(timezone.utc); return fit_model(tuple(CalibrationTrial(source,t,p,now+timedelta(seconds=i)) for i,(t,p) in enumerate(pairs)),source_id=source)
class DriftCusumCourt(unittest.TestCase):
    def test_stable_and_shift_are_distinct(self):
        a=model("s",[(1,1),(1,1),(0,0),(0,0)]); b=model("s",[(1,0),(1,0),(0,1),(0,1)]); self.assertEqual(classify_drift(compare_models(a,a),threshold=Fraction(1,2)),"STABLE"); self.assertEqual(classify_drift(compare_models(a,b),threshold=Fraction(1,2)),"DRIFT")
    def test_cusum_detects_error_shift(self):
        stable=prequential_cusum((0,0,0,0),target=Fraction(1,10),slack=Fraction(1,20),threshold=2); shifted=prequential_cusum((1,1,1,1),target=Fraction(1,10),slack=Fraction(1,20),threshold=2); self.assertFalse(stable.alarm); self.assertTrue(shifted.alarm)
if __name__=="__main__": unittest.main()
