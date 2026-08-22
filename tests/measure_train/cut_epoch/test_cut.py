import unittest
from datetime import datetime,timezone
from scripts.measure_train.cut_epoch.subject import Subject,Refused
from scripts.measure_train.cut_epoch.epoch import ProducerEpoch
from scripts.measure_train.cut_epoch.cut import EvidenceCut
class T(unittest.TestCase):
 def test_identity_and_duplicate(self):
  now=datetime.now(timezone.utc); e=ProducerEpoch(Subject("o/r","a"*40),1,"1"*64,now); c=EvidenceCut(1,(e,))
  self.assertEqual(len(c.cut_id),64)
  with self.assertRaises(Refused): EvidenceCut(1,(e,e))
