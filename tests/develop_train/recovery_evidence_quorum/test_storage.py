import unittest
from scripts.develop_train.recovery_evidence_quorum.storage import PersistenceNeed, Store, deterministic_failure_schedule, select_store, store_candidates

class TestStorage(unittest.TestCase):
    def test_reversible_store_candidates_and_seeded_failure(self):
        self.assertEqual(set(store_candidates()),set(Store))
        self.assertEqual(select_store(PersistenceNeed(transactional=True)),Store.SQLITE)
        self.assertEqual(deterministic_failure_schedule(7,.5,8),deterministic_failure_schedule(7,.5,8))
