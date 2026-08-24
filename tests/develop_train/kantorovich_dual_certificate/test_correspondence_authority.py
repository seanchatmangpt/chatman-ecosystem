import unittest
from scripts.develop_train.kantorovich_dual_certificate import *
S=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40+"#"+"b"*64)
ENG=[EngineWitness("BEAM","impl-beam","model-beam","s","t","o"),EngineWitness("WASM","impl-wasm","model-wasm","s","t","o")]
ORC=[OracleWitness("powl","p1","ip1","mp1","d"),OracleWitness("powl","p2","ip2","mp2","d"),OracleWitness("ocel","o1","io1","mo1","e"),OracleWitness("ocel","o2","io2","mo2","e")]
class T(unittest.TestCase):
    def test_correspondence_authority_receipt(self):
        self.assertTrue(require_engines(ENG)); self.assertTrue(require_oracles(ORC,"powl"))
        with self.assertRaises(Refused): admit(Action.DO)
        self.assertEqual(admit(Action.DO,"BRCE"),Action.DO)
        receipt=Receipt(S.key,"PARTIAL_ALIVE","p","d","c"); self.assertEqual(replay(receipt,receipt.digest),"REPLAY_MATCH")
        with self.assertRaises(Refused): replay(receipt,"0"*64)
    def test_engine_divergence_refuses(self):
        bad=[ENG[0],EngineWitness("WASM","impl-wasm","model-wasm","s","different","o")]
        with self.assertRaises(Refused): require_engines(bad)
