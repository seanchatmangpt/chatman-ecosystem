import unittest
from datetime import datetime,timezone
from scripts.develop_train.calibration_regime_quorum.frontier import build_frontier
from scripts.develop_train.calibration_regime_quorum.regime import CalibrationRegime
from scripts.develop_train.calibration_regime_quorum.subject import Refusal
class RegimeFrontierCourt(unittest.TestCase):
    def test_frontier_preserves_history(self):
        now=datetime.now(timezone.utc); r0=CalibrationRegime("s",0,"INSUFFICIENT",None,now); r1=CalibrationRegime("s",1,"INSUFFICIENT",None,now); f=build_frontier((r0,r1)); self.assertEqual(f.current.generation,1); self.assertEqual([r.generation for r in f.historical],[0])
    def test_divergent_current_refuses(self):
        now=datetime.now(timezone.utc); a=CalibrationRegime("s",1,"INSUFFICIENT",None,now); b=CalibrationRegime("s",1,"DRIFT",None,now)
        with self.assertRaisesRegex(Refusal,"DIVERGENT_REGIME_FRONTIER"): build_frontier((a,b))
if __name__=="__main__": unittest.main()
