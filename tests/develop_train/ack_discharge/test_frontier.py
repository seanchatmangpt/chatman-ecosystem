import unittest
from scripts.develop_train.ack_discharge.frontier import AckFrontier
from scripts.develop_train.ack_discharge.subject import Subject
class T(unittest.TestCase):
 def test_idempotent(self):
  s=Subject('o/c','a'*40);f=AckFrontier.from_consumers([(s,False)]);self.assertTrue(f.record(s,'r'));self.assertFalse(f.record(s,'r'))
