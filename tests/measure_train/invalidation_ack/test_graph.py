import unittest
from scripts.measure_train.invalidation_ack.subject import Subject,Refused
from scripts.measure_train.invalidation_ack.graph import affected_consumers
class T(unittest.TestCase):
 def test_depth_and_cycle(self):
  a,b,c=Subject("o/a","a"*40),Subject("o/b","b"*40),Subject("o/c","c"*40)
  self.assertEqual(affected_consumers([(a,b),(b,c)],a),((b,1),(c,2)))
  with self.assertRaises(Refused): affected_consumers([(a,b),(b,a)],a)
