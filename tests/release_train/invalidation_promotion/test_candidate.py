import unittest
from scripts.release_train.invalidation_promotion.candidate import candidates, select_candidate
class T(unittest.TestCase):
 def test_reversible_alternatives(self):
  self.assertEqual({c.name for c in candidates()},{'memory','jsonl','sqlite'})
  self.assertEqual(select_candidate(require_transactional=True).name,'sqlite')
