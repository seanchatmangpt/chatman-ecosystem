import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.cut_epoch.subject import Subject,Refused
from scripts.measure_train.cut_epoch.epoch import ProducerEpoch
from scripts.measure_train.cut_epoch.cut import EvidenceCut
from scripts.measure_train.cut_epoch.lease import CutLease
from scripts.measure_train.cut_epoch.supersession import CutSupersession
from scripts.measure_train.cut_epoch.qualify import qualify
from scripts.measure_train.cut_epoch.replay import replay
class T(unittest.TestCase):
 def test_old_cut_invalid_after_producer_advance_new_cut_qualifies(self):
  now=datetime.now(timezone.utc); consumer=Subject("c/root","c"*40)
  olde=ProducerEpoch(Subject("p/a","a"*40),1,"1"*64,now); newe=ProducerEpoch(Subject("p/a","b"*40),2,"2"*64,now+timedelta(seconds=1))
  old=EvidenceCut(1,(olde,)); new=EvidenceCut(2,(newe,)); edge=CutSupersession(new.cut_id,old.cut_id,2,1,"PRODUCER_ADVANCED")
  oldlease=CutLease(old.cut_id,now,now+timedelta(hours=1))
  with self.assertRaises(Refused): qualify(consumer,(old,new),(edge,),oldlease,(newe,),( ("p/a","PASS"),),now+timedelta(seconds=2))
  newlease=CutLease(new.cut_id,now+timedelta(seconds=1),now+timedelta(hours=1))
  q=qualify(consumer,(old,new),(edge,),newlease,(newe,),( ("p/a","PASS"),),now+timedelta(seconds=2))
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
