import unittest
from datetime import datetime,timezone,timedelta
from scripts.develop_train.epoch_discharge.identity import Subject
from scripts.develop_train.epoch_discharge.epoch import InvalidationEpoch
from scripts.develop_train.epoch_discharge.witness import Witness,WitnessKind,DischargeResult
from scripts.develop_train.epoch_discharge.strategy import CompletionStrategy
from scripts.develop_train.epoch_discharge.engine import qualify
from scripts.develop_train.epoch_discharge.receipt import replay
class T(unittest.TestCase):
 def test_current_epoch_full_discharge_qualifies_without_do(self):
  n=datetime.now(timezone.utc)-timedelta(seconds=1); p=Subject("a/p@"+"a"*40); c=Subject("a/c@"+"b"*40); e=InvalidationEpoch(p,3,"evt","c"*64,n)
  d=Witness(p,c,3,"evt",WitnessKind.DELIVERY,"d","d"*64,n+timedelta(milliseconds=1)); a=Witness(p,c,3,"evt",WitnessKind.ACK,"a","e"*64,n+timedelta(milliseconds=2),parent_receipt=d.receipt_digest); s=Witness(p,c,3,"evt",WitnessKind.DISCHARGE,"s","f"*64,n+timedelta(milliseconds=3),parent_receipt=a.receipt_digest,result=DischargeResult.REQUALIFIED)
  q=qualify(e,(c.value,),(d,a,s),CompletionStrategy.ALL); self.assertTrue(q.complete); self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertFalse(q.actuation_performed); self.assertTrue(replay(q.receipt))
  stale=Witness(p,c,2,"evt",WitnessKind.DELIVERY,"old","1"*64,n+timedelta(milliseconds=1))
  with self.assertRaisesRegex(ValueError,"STALE_INVALIDATION_EPOCH"): qualify(e,(c.value,),(stale,),CompletionStrategy.ALL)
