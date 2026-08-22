import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.recovery_witness.subject import Subject,Refused
from scripts.measure_train.recovery_witness.context import RecoveryContext
from scripts.measure_train.recovery_witness.witness import CompatibilityWitness
from scripts.measure_train.recovery_witness.lease import WitnessLease
from scripts.measure_train.recovery_witness.proof import RecoveryProof
from scripts.measure_train.recovery_witness.qualify import qualify
from scripts.measure_train.recovery_witness.replay import replay
class T(unittest.TestCase):
 def test_witness_must_follow_after_context_movement(self):
  now=datetime.now(timezone.utc); consumer=Subject("c/r","c"*40); producer=Subject("p/r","a"*40)
  before=RecoveryContext(producer,"cut1","1"*64,"2"*64,1)
  after=RecoveryContext(producer,"cut2","1"*64,"3"*64,2)
  later=RecoveryContext(producer,"cut3","1"*64,"4"*64,3)
  w=CompatibilityWitness(before,after,"SEMANTIC_EQUIVALENT","PASS","w",now,"5"*64,"6"*64)
  p=RecoveryProof("REBIND_EQUIVALENT",w,WitnessLease(now-timedelta(seconds=1),now+timedelta(minutes=5)),"p")
  q=qualify(consumer,before,after,p,[w],now)
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  with self.assertRaises(Refused): qualify(consumer,before,later,p,[w],now)
