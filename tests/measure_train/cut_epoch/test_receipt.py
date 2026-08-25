import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.cut_epoch.subject import Subject
from scripts.measure_train.cut_epoch.epoch import ProducerEpoch
from scripts.measure_train.cut_epoch.cut import EvidenceCut
from scripts.measure_train.cut_epoch.lease import CutLease
from scripts.measure_train.cut_epoch.receipt import manufacture_receipt
class T(unittest.TestCase):
 def test_deterministic_no_do(self):
  now=datetime(2026,8,22,tzinfo=timezone.utc); e=ProducerEpoch(Subject("p/r","a"*40),1,"1"*64,now); c=EvidenceCut(1,(e,)); l=CutLease(c.cut_id,now,now+timedelta(hours=1))
  a=manufacture_receipt(Subject("c/r","b"*40),c,l,(("p/r","PASS"),),"PARTIAL_ALIVE"); b=manufacture_receipt(Subject("c/r","b"*40),c,l,(("p/r","PASS"),),"PARTIAL_ALIVE")
  self.assertEqual(a,b); self.assertFalse(a["body"]["actuation_performed"])
