import unittest
from scripts.release_train.promotion_intent_lease.candidate import PersistenceNeed,select,candidates,Store
class T(unittest.TestCase):
 def test_reversible_candidates(self):
  self.assertEqual(set(candidates()),{Store.MEMORY,Store.JSONL,Store.SQLITE})
  self.assertEqual(select(PersistenceNeed(transactional=True)),Store.SQLITE)
