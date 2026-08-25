import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.requalification_epoch.subject import Subject,Refused
from scripts.measure_train.requalification_epoch.epoch import InvalidationEpoch
from scripts.measure_train.requalification_epoch.witness import Witness
from scripts.measure_train.requalification_epoch.admission import admit_witness
class T(unittest.TestCase):
 def test_ack_requires_exact_delivery_parent(self):
  now=datetime.now(timezone.utc); p=Subject("p/r","a"*40); c=Subject("c/r","b"*40); e=InvalidationEpoch(p,1,"e",now,"1"*64)
  d=Witness(c,p,1,"e","DELIVERY","d",now+timedelta(seconds=1)); a=Witness(c,p,1,"e","ACKNOWLEDGEMENT","a",now+timedelta(seconds=2),parent_id="wrong")
  with self.assertRaisesRegex(Refused,"CAUSAL_WITNESS_GAP"): admit_witness(e,a,[d])
