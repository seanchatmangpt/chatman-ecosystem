import unittest
from scripts.develop_train.selection_intent_runtime.persistence import *
class TestPersistence(unittest.TestCase):
 def test_candidates_and_transactional_selection(self):
  self.assertEqual([c.kind for c in CANDIDATES],[StoreKind.MEMORY,StoreKind.JSONL,StoreKind.SQLITE]); self.assertEqual(select_store(PersistenceNeed(transactional=True)).kind,StoreKind.SQLITE)
