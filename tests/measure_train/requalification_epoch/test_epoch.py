import unittest
from datetime import datetime,timezone
from scripts.measure_train.requalification_epoch.subject import Subject,Refused
from scripts.measure_train.requalification_epoch.epoch import InvalidationEpoch
class T(unittest.TestCase):
 def test_epoch_contract(self):
  e=InvalidationEpoch(Subject("o/r","a"*40),1,"ev",datetime.now(timezone.utc),"1"*64); self.assertEqual(e.generation,1)
  with self.assertRaises(Refused): InvalidationEpoch(e.producer,-1,"ev",datetime.now(timezone.utc),"1"*64)
