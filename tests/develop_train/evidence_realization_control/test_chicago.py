import unittest
from scripts.develop_train.evidence_realization_control import *
class T(unittest.TestCase):
 def test_end_to_end(self):
  s=Subject.parse('seanchatmangpt/chatman-ecosystem@'+'d'*40)
  ns=[EvidenceNode('semantic',s,'semantic',4,Interval(.9,.98),'beam','m1','r1'),EvidenceNode('realized',s,'realization',4,Interval(.8,.95),'wasm','m2','r2')]
  q=qualify(ns,REQUIRED,['ALIVE','PARTIAL_ALIVE']); self.assertEqual(q.standing,'PARTIAL_ALIVE'); self.assertEqual(replay(q.receipt,q.receipt.digest()),'REPLAY_MATCH')
  red=qualify(ns,REQUIRED,['PARTIAL_ALIVE','BUILD_BROKEN']); self.assertEqual(red.standing,'BUILD_BROKEN'); self.assertIsNone(red.receipt)
