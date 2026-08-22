import unittest
from datetime import datetime,timezone
from scripts.measure_train.consistent_cut.subject import Subject,Refused
from scripts.measure_train.consistent_cut.epoch import EpochStamp
class T(unittest.TestCase):
 def test_epoch_contract(self):
  e=EpochStamp(Subject("o/r","a"*40),1,"1"*64,datetime.now(timezone.utc))
  self.assertEqual(e.generation,1)
  with self.assertRaises(Refused): EpochStamp(e.subject,-1,"1"*64,datetime.now(timezone.utc))
