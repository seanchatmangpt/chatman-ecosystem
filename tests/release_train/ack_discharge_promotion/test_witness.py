import unittest
from datetime import datetime, timezone
from scripts.release_train.ack_discharge_promotion.subject import Subject
from scripts.release_train.ack_discharge_promotion.witness import Witness, WitnessRefusal
S=Subject.parse("o/r@"+"a"*40)
class T(unittest.TestCase):
    def test_discharge(self): self.assertEqual(Witness(S,"e","DISCHARGED",datetime.now(timezone.utc),"REQUALIFIED").result,"REQUALIFIED")
    def test_alive_refuses(self):
        with self.assertRaises(WitnessRefusal): Witness(S,"e","DISCHARGED",datetime.now(timezone.utc),"ALIVE")
