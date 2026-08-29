import unittest
from scripts.release_train.promotion_epoch.rollback import RollbackPlan
class T(unittest.TestCase):
 def test_reversible(self): self.assertFalse(RollbackPlan("a"*40,"b"*40,"replay").external_compensation_required)
 def test_external_compensation_refuses(self):
  with self.assertRaises(ValueError): RollbackPlan("a"*40,"b"*40,"replay",True)
