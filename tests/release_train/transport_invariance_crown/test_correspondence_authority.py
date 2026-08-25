import unittest
from scripts.release_train.transport_invariance_crown import EngineEvidence, OracleEvidence, RegionEvidence, REQUIRED_FAILURES, admit_correspondence, admit_failure_worlds, ActionClass, admit_action, Receipt, replay, Refused

class CorrespondenceAuthorityCourt(unittest.TestCase):
    def test_independence_tls_failure_and_brce(self):
        triple=('s'*64,'t'*64,'o'*64)
        engines=(EngineEvidence('BEAM','beam-impl','beam-model',*triple),EngineEvidence('WASM','wasm-impl','wasm-model',*triple))
        oracles=(OracleEvidence('POWL','oracle-a','formal-a','p'*64),OracleEvidence('OCEL','oracle-b','formal-b','q'*64))
        regions=(RegionEvidence('h1','us-west','1'*64,True,7),RegionEvidence('h2','us-east','2'*64,True,7))
        admit_correspondence(engines,oracles,regions,7)
        admit_failure_worlds({k:True for k in REQUIRED_FAILURES})
        with self.assertRaisesRegex(Refused,'DO_REQUIRES_BRCE'): admit_action(ActionClass.DO)
        self.assertEqual(admit_action(ActionClass.DO,'BRCE'),ActionClass.DO)
        r=Receipt('x','s',7,'PARTIAL_ALIVE','e'*64,'MINIMAX').seal(); self.assertEqual(replay(r),'REPLAY_MATCH')
