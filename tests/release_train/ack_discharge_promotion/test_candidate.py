import unittest
from scripts.release_train.ack_discharge_promotion.candidate import select
class T(unittest.TestCase):
    def test_memory(self): self.assertEqual(select(require_durable=False,require_transactional=False).name,"MEMORY")
    def test_sqlite(self): self.assertEqual(select(require_durable=True,require_transactional=True).name,"SQLITE")
