import unittest
from scripts.develop_train.epoch_discharge.persistence import PersistenceNeed,Store,candidates,select_store
class T(unittest.TestCase):
 def test_alternatives_preserved(self):
  self.assertEqual(candidates(),(Store.MEMORY,Store.JSONL,Store.SQLITE)); self.assertEqual(select_store(PersistenceNeed(transactional=True)),Store.SQLITE)
