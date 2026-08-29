import unittest
from scripts.release_train.receipt import manufacture,replay,ReceiptRefusal

class ReceiptTests(unittest.TestCase):
    def test_deterministic_replay(self):
        a=manufacture({"b":2,"a":1}); b=manufacture({"a":1,"b":2})
        self.assertEqual(a,b); self.assertTrue(replay(a))
    def test_tamper_refuses(self):
        doc=manufacture({"a":1}); doc["a"]=2
        with self.assertRaisesRegex(ReceiptRefusal,"RECEIPT_MISMATCH"):
            replay(doc)
