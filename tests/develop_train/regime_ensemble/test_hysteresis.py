import unittest
from scripts.develop_train.regime_ensemble.hysteresis import HysteresisState, RegimeState, advance
class TestHysteresis(unittest.TestCase):
    def test_requires_entry_and_clear_streaks(self):
        s=advance(HysteresisState(),True); self.assertEqual(s.state,RegimeState.SUSPECT)
        s=advance(s,True); self.assertEqual(s.state,RegimeState.DRIFT)
        s=advance(s,False); self.assertEqual(s.state,RegimeState.DRIFT)
        s=advance(advance(s,False),False); self.assertEqual(s.state,RegimeState.STABLE)
if __name__ == "__main__": unittest.main()
