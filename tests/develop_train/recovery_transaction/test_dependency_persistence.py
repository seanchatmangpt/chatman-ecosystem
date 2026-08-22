import unittest
from scripts.develop_train.recovery_transaction.subject import Refusal
from scripts.develop_train.recovery_transaction.dependency import DependencyGraph
from scripts.develop_train.recovery_transaction.persistence import PersistenceNeed, Store, candidates, select

class T(unittest.TestCase):
    def test_transitive_blocker_and_cycle_refusal(self):
        graph = DependencyGraph({"release-control": ("gymact",), "gymact": ("ggen",), "ggen": ()})
        self.assertEqual(graph.blockers("release-control", {"ggen": "BUILD_BROKEN"}), ("ggen",))
        with self.assertRaises(Refusal):
            DependencyGraph({"a": ("b",), "b": ("a",)})
    def test_storage_candidates_remain_reversible(self):
        self.assertEqual(candidates(), (Store.MEMORY, Store.JSONL, Store.SQLITE))
        self.assertEqual(select(PersistenceNeed(transactional=True)), Store.SQLITE)
        self.assertEqual(select(PersistenceNeed(durable=True)), Store.JSONL)

if __name__ == "__main__":
    unittest.main()
