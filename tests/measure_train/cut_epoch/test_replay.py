import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.cut_epoch.subject import Subject,Refused
from scripts.measure_train.cut_epoch.epoch import ProducerEpoch
from scripts.measure_train.cut_epoch.cut import EvidenceCut
from scripts.measure_train.cut_epoch.lease import CutLease
from scripts.measure_train.cut_epoch.receipt import manufacture_receipt
from scripts.measure_train.cut_epoch.replay import replay
class T(unittest.TestCase):
 def test_tamper(self):
  now=datetime.now(timezone.utc); e=ProducerEpoch(Subject("p/r","a"*40),1,"1"*64,now); c=EvidenceCut(1,(e,)); l=CutLease(c.cut_id,now,now+timedelta(hours=1)); r=manufacture_receipt(Subject("c/r","b"*40),c,l,(),"UNKNOWN")
  self.assertEqual(replay(r),"REPLAY_MATCH"); r["body"]["actuation_performed"]=True
  with self.assertRaises(Refused): replay(r)
