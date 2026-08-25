import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.cut_epoch.subject import Subject,Refused
from scripts.measure_train.cut_epoch.epoch import ProducerEpoch
from scripts.measure_train.cut_epoch.cut import EvidenceCut
from scripts.measure_train.cut_epoch.lease import CutLease
from scripts.measure_train.cut_epoch.admission import admit_cut
class T(unittest.TestCase):
 def test_stale_cut_refuses(self):
  now=datetime.now(timezone.utc); olde=ProducerEpoch(Subject("p/r","a"*40),1,"1"*64,now); newe=ProducerEpoch(Subject("p/r","b"*40),2,"2"*64,now)
  old=EvidenceCut(1,(olde,)); new=EvidenceCut(2,(newe,)); lease=CutLease(old.cut_id,now-timedelta(seconds=1),now+timedelta(hours=1))
  with self.assertRaises(Refused): admit_cut(old,lease,new,(newe,),now)
