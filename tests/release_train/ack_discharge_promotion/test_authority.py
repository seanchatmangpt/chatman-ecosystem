import unittest
from scripts.release_train.ack_discharge_promotion.authority import require, AuthorityRefusal
class T(unittest.TestCase):
    def test_construct(self): self.assertIsNone(require("CONSTRUCT"))
    def test_do(self):
        with self.assertRaises(AuthorityRefusal): require("DO")
