import unittest
from dataclasses import replace
from scripts.measure_train.replay import verify
from scripts.measure_train.receipts import manufacture
from scripts.measure_train.identity import Refused
class ReplayCourt(unittest.TestCase):
    def test_match(self):
        r=manufacture('o/r@'+'a'*40,()); self.assertTrue(verify(r,()))
    def test_tamper_refuses(self):
        r=manufacture('o/r@'+'a'*40,())
        with self.assertRaises(Refused): verify(replace(r,observation_digest='0'*64),())
if __name__=='__main__': unittest.main()
