import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.requalification_epoch.subject import Subject,Refused
from scripts.measure_train.requalification_epoch.epoch import InvalidationEpoch
from scripts.measure_train.requalification_epoch.witness import Witness
from scripts.measure_train.requalification_epoch.admission import admit_witness
class T(unittest.TestCase):
 def test_ack_cannot_cross_epoch(self):
  now=datetime.now(timezone.utc); p=Subject("p/r","a"*40); c=Subject("c/r","b"*40); e=InvalidationEpoch(p,2,"e2",now,"2"*64)
  d=Witness(c,p,2,"e2","DELIVERY","d2",now+timedelta(seconds=1))
  a=Witness(c,p,1,"e1","ACKNOWLEDGEMENT","a1",now+timedelta(seconds=2),parent_id="d1")
  with self.assertRaises(Refused): admit_witness(e,a,[d])
