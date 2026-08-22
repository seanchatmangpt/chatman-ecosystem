import unittest
from scripts.measure_train.delta.lineage import LineageObservation
class T(unittest.TestCase):
 def test_closed_unmerged_refuses(self):
  self.assertEqual(LineageObservation(1,'open',False,'a'*40,'b'*40).admit(),"ADMITTED_OPEN_HEAD")
  with self.assertRaises(ValueError): LineageObservation(1,'closed',False,'a'*40,'b'*40).admit()
