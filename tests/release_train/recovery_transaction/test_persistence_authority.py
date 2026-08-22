import unittest
from scripts.release_train.recovery_transaction import *
class T(unittest.TestCase):
 def test_candidates_and_selection(self):
  self.assertEqual(len(candidates()),3);self.assertEqual(select_store(PersistenceNeed(transactional=True)),Store.SQLITE);self.assertEqual(select_store(PersistenceNeed(durable=True)),Store.JSONL)
 def test_do_refuses(self):
  with self.assertRaisesRegex(Refusal,'BRCE_REQUIRED'):require(ActionClass.DO)
if __name__=='__main__':unittest.main()
