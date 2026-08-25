import unittest
from dataclasses import replace
from scripts.release_train.certificate_federation_realization_crown import *
from scripts.release_train.certificate_federation_realization_crown.refusal import Refused
class TestAuthorityReplay(unittest.TestCase):
    def test_brce_and_receipt(self):
        with self.assertRaises(Refused): admit_action(Action("DO"))
        self.assertEqual("DO",admit_action(Action("DO","BRCE")).authority)
        s=Subject("o/r","4"*40,"x")
        c=Calibration(1,10,0.0,0.0,0.0,"a"*64)
        q=qualify(s,c,(),0.9)
        self.assertEqual("PARTIAL_ALIVE",q.standing)
        self.assertEqual("REPLAY_MATCH",replay(q.receipt))
        with self.assertRaises(Refused): replay(replace(q.receipt,standing="ALIVE"))
