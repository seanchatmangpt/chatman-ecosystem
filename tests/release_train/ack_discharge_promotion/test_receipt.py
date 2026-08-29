import unittest
from scripts.release_train.ack_discharge_promotion.receipt import manufacture,replay,Receipt
class T(unittest.TestCase):
    def test_replay(self):
        r=manufacture({"x":1}); self.assertTrue(replay(r))
        self.assertFalse(replay(Receipt(r.schema,r.digest,{**r.body,"x":2})))
