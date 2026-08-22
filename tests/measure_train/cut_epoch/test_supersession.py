import unittest
from scripts.measure_train.cut_epoch.supersession import CutSupersession
from scripts.measure_train.cut_epoch.subject import Refused
class T(unittest.TestCase):
 def test_forward_only(self):
  self.assertEqual(CutSupersession("a"*64,"b"*64,2,1,"PRODUCER_ADVANCED").newer_generation,2)
  with self.assertRaises(Refused): CutSupersession("a"*64,"b"*64,1,1,"PRODUCER_ADVANCED")
