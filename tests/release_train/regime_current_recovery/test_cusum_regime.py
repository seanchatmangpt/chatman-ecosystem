import unittest
from scripts.release_train.regime_current_recovery.cusum import detect_error_shift
from scripts.release_train.regime_current_recovery.regime import RegimeState,advance
from fixtures import model
class T(unittest.TestCase):
 def test_shift(self):
  self.assertTrue(detect_error_shift([0,0,1,1,1,1],reference=.1,slack=.05,threshold=1.5).alarm); first=advance(None,model(),RegimeState.STABLE,'CUSUM'); second=advance(first,model(errors=1),RegimeState.DRIFT,'CUSUM'); self.assertEqual((first.generation,second.generation),(0,1))
 def test_clean(self): self.assertFalse(detect_error_shift([0,0,0,0],reference=.1,threshold=1).alarm)
