import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.requalification_epoch.subject import Subject,Refused
from scripts.measure_train.requalification_epoch.epoch import InvalidationEpoch
from scripts.measure_train.requalification_epoch.witness import Witness
from scripts.measure_train.requalification_epoch.admission import admit_witness
class T(unittest.TestCase):
 def test_old_discharge_cannot_discharge_new_epoch(self):
  now=datetime.now(timezone.utc); p=Subject("p/r","a"*40); c=Subject("c/r","b"*40); e=InvalidationEpoch(p,3,"e3",now,"3"*64)
  old=Witness(c,p,2,"e2","DISCHARGE","x",now+timedelta(seconds=2),"REQUALIFIED","a2")
  with self.assertRaisesRegex(Refused,"STALE_INVALIDATION_EPOCH"): admit_witness(e,old,[])
