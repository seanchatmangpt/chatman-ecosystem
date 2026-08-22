import unittest

from scripts.develop_train.calibrated_recovery_quorum.authority import (
    ActionClass,
    require_nonconsequential,
)
from scripts.develop_train.calibrated_recovery_quorum.persistence import (
    PersistenceNeed,
    Store,
    candidates,
    select_store,
)


class TestPersistenceAuthority(unittest.TestCase):
    def test_reversible_candidates_and_selector(self):
        self.assertEqual(candidates(), (Store.MEMORY, Store.JSONL, Store.SQLITE))
        self.assertEqual(select_store(PersistenceNeed(transactional=True)), Store.SQLITE)

    def test_direct_do_refuses(self):
        with self.assertRaisesRegex(PermissionError, "BRCE_REQUIRED"):
            require_nonconsequential(ActionClass.DO)
