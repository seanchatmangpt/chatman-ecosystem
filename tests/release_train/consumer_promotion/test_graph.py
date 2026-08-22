import unittest
from scripts.release_train.consumer_promotion.graph import topo,propagate
class T(unittest.TestCase):
 def test_blocker(self):
  d={"a":{"b"},"b":set()}; o=topo(d); self.assertEqual(propagate(o,{"a":"ALIVE","b":"BUILD_BROKEN"},d)["a"],"BLOCKED")
 def test_cycle(self):
  with self.assertRaisesRegex(ValueError,"CYCLE"): topo({"a":{"b"},"b":{"a"}})
