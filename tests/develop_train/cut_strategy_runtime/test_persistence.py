import unittest
from scripts.develop_train.cut_strategy_runtime.persistence import PersistenceNeed, StoreKind, candidates, select_store
class PersistenceCourt(unittest.TestCase):
    def test_reversible_candidates_and_transactional_selection(self):
        self.assertEqual(candidates(), (StoreKind.MEMORY,StoreKind.JSONL,StoreKind.SQLITE))
        self.assertEqual(select_store(PersistenceNeed(transactional=True)), StoreKind.SQLITE)
        self.assertEqual(select_store(PersistenceNeed(durable=True)), StoreKind.JSONL)
if __name__ == '__main__': unittest.main()
