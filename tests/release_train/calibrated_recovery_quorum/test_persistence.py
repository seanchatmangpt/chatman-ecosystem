import unittest
from scripts.release_train.calibrated_recovery_quorum.persistence import *
class T(unittest.TestCase):
 def test_reversible_selection(self):
  self.assertEqual(CANDIDATES,("MEMORY","JSONL","SQLITE")); self.assertEqual(select_store(PersistenceNeed(transactional=True)),"SQLITE")
