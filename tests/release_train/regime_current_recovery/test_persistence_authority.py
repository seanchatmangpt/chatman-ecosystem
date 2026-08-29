import unittest
from scripts.release_train.regime_current_recovery.persistence import Store,PersistenceNeed,candidates,select
from scripts.release_train.regime_current_recovery.authority import ActionClass,require
from scripts.release_train.regime_current_recovery.subject import Refusal
class T(unittest.TestCase):
 def test_stores(self): self.assertEqual(set(candidates()),set(Store)); self.assertEqual(select(PersistenceNeed(transactional=True)),Store.SQLITE)
 def test_do(self):
  require(ActionClass.CONSTRUCT)
  with self.assertRaisesRegex(Refusal,'BRCE_REQUIRED'): require(ActionClass.DO)
