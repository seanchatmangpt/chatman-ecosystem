import unittest
from datetime import datetime,timezone
from scripts.measure_train.cut_epoch.subject import Subject,Refused
from scripts.measure_train.cut_epoch.epoch import ProducerEpoch
class T(unittest.TestCase):
 def test_epoch(self):
  e=ProducerEpoch(Subject("o/r","a"*40),1,"1"*64,datetime.now(timezone.utc)); self.assertEqual(e.generation,1)
  with self.assertRaises(Refused): ProducerEpoch(e.subject,-1,"1"*64,datetime.now(timezone.utc))
