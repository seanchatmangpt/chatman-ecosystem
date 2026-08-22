import unittest
from scripts.measure_train.invalidation_ack.subject import Subject
from scripts.measure_train.invalidation_ack.standing import standing
class T(unittest.TestCase):
 def test_requalified_caps_partial(self):
  c=Subject("c/r","b"*40)
  self.assertEqual(standing([(c,1,"REQUALIFIED")]),"PARTIAL_ALIVE")
  self.assertEqual(standing([(c,1,"PENDING_ACK")]),"UNKNOWN")
