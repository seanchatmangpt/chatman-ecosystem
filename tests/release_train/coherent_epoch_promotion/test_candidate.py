import unittest
from scripts.release_train.coherent_epoch_promotion.candidate import select_candidate,Persistence,candidates
class T(unittest.TestCase):
 def test_preserves_reversible_choices(self):
  self.assertEqual(len(candidates()),3)
  self.assertEqual(select_candidate(True).persistence,Persistence.SQLITE)
