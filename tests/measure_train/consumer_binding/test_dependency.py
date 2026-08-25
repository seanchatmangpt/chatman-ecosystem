import unittest
from scripts.measure_train.consumer_binding.dependency import propagate_consumer_standing
class T(unittest.TestCase):
 def test_block(self):
  r=propagate_consumer_standing(["consumer","producer"],[("consumer","producer")],{"consumer":"PARTIAL_ALIVE","producer":"BUILD_BROKEN"})
  self.assertEqual(r["consumer"],"BLOCKED")
