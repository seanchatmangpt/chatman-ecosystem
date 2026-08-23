import unittest
from scripts.develop_train.replicated_evidence_state.merkle import merkle_root

class MerkleTest(unittest.TestCase):
    def test_order_independent_root(self):
        ds=["a"*64,"b"*64,"c"*64]
        self.assertEqual(merkle_root(ds),merkle_root(list(reversed(ds))))
        self.assertEqual(len(merkle_root(ds)),64)
