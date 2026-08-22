import unittest
from scripts.measure_train.consumer_binding.subject import Subject,Refused
from scripts.measure_train.consumer_binding.producer import ProducerEvidence
class T(unittest.TestCase):
 def test_receipt(self):
  p=ProducerEvidence(Subject("o/r","a"*40),"b"*64,"schema/1","PARTIAL_ALIVE")
  self.assertEqual(p.standing,"PARTIAL_ALIVE")
  with self.assertRaises(Refused): ProducerEvidence(p.subject,"bad","x","PARTIAL_ALIVE")
