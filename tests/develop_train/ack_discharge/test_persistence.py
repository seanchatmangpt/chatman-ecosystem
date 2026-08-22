import unittest
from scripts.develop_train.ack_discharge.persistence import *
class T(unittest.TestCase):
 def test_selection(self):
  self.assertEqual(len(candidates()),3);self.assertEqual(select(StoreRequirements(transactional=True)),StoreKind.SQLITE);self.assertEqual(select(StoreRequirements(durable=True)),StoreKind.JSONL)
