import unittest
from scripts.release_train.detector_consensus_recovery.hysteresis import HysteresisState,advance
from scripts.release_train.detector_consensus_recovery.consensus import Consensus
class Court(unittest.TestCase):
 def test_spike_cannot_create_drift(self): self.assertEqual(advance(HysteresisState(),Consensus("DRIFT_CONFIRMED",(),2,0)).regime,"SUSPECT")
 def test_asymmetric_entry_clear(self):
  d=Consensus("DRIFT_CONFIRMED",(),2,0); s=advance(advance(HysteresisState(),d),d); self.assertEqual(s.regime,"DRIFT")
  stable=Consensus("STABLE_CONFIRMED",(),0,2); s=advance(s,stable); self.assertEqual(s.regime,"DRIFT")
