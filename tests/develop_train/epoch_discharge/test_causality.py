import unittest
from datetime import datetime,timezone,timedelta
from scripts.develop_train.epoch_discharge.identity import Subject
from scripts.develop_train.epoch_discharge.epoch import InvalidationEpoch
from scripts.develop_train.epoch_discharge.witness import Witness,WitnessKind
from scripts.develop_train.epoch_discharge.admission import admit_witness
class T(unittest.TestCase):
 def test_ack_requires_exact_delivery_receipt(self):
  n=datetime.now(timezone.utc)-timedelta(seconds=1); p=Subject("a/p@"+"a"*40); c=Subject("a/c@"+"b"*40); e=InvalidationEpoch(p,1,"e","c"*64,n); d=Witness(p,c,1,"e",WitnessKind.DELIVERY,"d","d"*64,n+timedelta(milliseconds=1)); a=Witness(p,c,1,"e",WitnessKind.ACK,"a","e"*64,n+timedelta(milliseconds=2),parent_receipt="f"*64)
  with self.assertRaisesRegex(ValueError,"CAUSAL_RECEIPT_MISMATCH"): admit_witness(e,a,{(c.value,"DELIVERY"):d})
