import unittest
from scripts.release_train.regime_current_recovery.frontier import build_frontier
from scripts.release_train.regime_current_recovery.regime import CalibrationRegime,RegimeState
from scripts.release_train.regime_current_recovery.admission import admit_current
from scripts.release_train.regime_current_recovery.subject import Refusal
from fixtures import SUBJECT,NOW,model,frontier,witness
class T(unittest.TestCase):
 def test_current(self): f=frontier(); admit_current(witness(front=f),f,NOW)
 def test_stale(self):
  with self.assertRaisesRegex(Refusal,'STALE_CALIBRATION_REGIME'): admit_current(witness(generation=2),frontier(generation=3),NOW)
 def test_drift(self):
  f=frontier(state=RegimeState.DRIFT)
  with self.assertRaisesRegex(Refusal,'CALIBRATION_DRIFTED'): admit_current(witness(front=f),f,NOW)
 def test_divergent(self):
  m=model(); regs=[CalibrationRegime(m,2,RegimeState.STABLE,'A'),CalibrationRegime(m,2,RegimeState.STABLE,'B')]
  with self.assertRaisesRegex(Refusal,'DIVERGENT_REGIME_FRONTIER'): build_frontier(SUBJECT,'s1',regs)
