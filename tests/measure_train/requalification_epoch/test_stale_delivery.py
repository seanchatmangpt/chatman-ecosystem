import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.requalification_epoch.subject import Subject,Refused
from scripts.measure_train.requalification_epoch.epoch import InvalidationEpoch
from scripts.measure_train.requalification_epoch.witness import Witness
from scripts.measure_train.requalification_epoch.admission import admit_witness
class T(unittest.TestCase):
 def test_prior_epoch_delivery_refuses(self):
  now=datetime.now(timezone.utc); p=Subject("p/r","a"*40); c=Subject("c/r","b"*40); e=InvalidationEpoch(p,2,"e2",now,"2"*64)
  w=Witness(c,p,1,"e1","DELIVERY","d1",now+timedelta(seconds=1))
  with self.assertRaisesRegex(Refused,"STALE_INVALIDATION_EPOCH"): admit_witness(e,w,[])
