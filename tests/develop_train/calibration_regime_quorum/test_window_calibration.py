import unittest
from datetime import datetime,timedelta,timezone
from fractions import Fraction
from scripts.develop_train.calibration_regime_quorum.calibration import fit_model
from scripts.develop_train.calibration_regime_quorum.subject import Refusal
from scripts.develop_train.calibration_regime_quorum.trials import CalibrationTrial
from scripts.develop_train.calibration_regime_quorum.windows import CalibrationWindow
class WindowCalibrationCourt(unittest.TestCase):
    def test_half_open_window_and_model(self):
        start=datetime(2026,8,22,tzinfo=timezone.utc); pairs=[(1,1),(1,1),(0,0),(0,0),(1,0)]; rows=tuple(CalibrationTrial("s",t,p,start+timedelta(minutes=i)) for i,(t,p) in enumerate(pairs)); selected=CalibrationWindow(start,start+timedelta(minutes=4)).select(rows,source_id="s")
        self.assertEqual(len(selected),4); model=fit_model(selected,source_id="s"); self.assertEqual(model.tpr,Fraction(3,4)); self.assertEqual(model.fpr,Fraction(1,4)); self.assertEqual(model.brier,0)
    def test_under_support_refuses(self):
        now=datetime.now(timezone.utc); rows=(CalibrationTrial("s",True,True,now),)
        with self.assertRaisesRegex(Refusal,"INSUFFICIENT_CALIBRATION_SUPPORT"): fit_model(rows,source_id="s")
if __name__=="__main__": unittest.main()
