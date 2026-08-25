import unittest
from fractions import Fraction
from scripts.measure_train.federation_convergence_kinetics_msa.subject import Subject
from scripts.measure_train.federation_convergence_kinetics_msa.frontier import KineticsModel
from scripts.measure_train.federation_convergence_kinetics_msa.capability import Capability
from scripts.measure_train.federation_convergence_kinetics_msa.dependence import EffectiveEpisodes
from scripts.measure_train.federation_convergence_kinetics_msa.receipt import manufacture
from scripts.measure_train.federation_convergence_kinetics_msa.replay import replay
from scripts.measure_train.federation_convergence_kinetics_msa.refusal import Refused

class TestReceiptReplay(unittest.TestCase):
    def test_tampering_refuses(self):
        receipt = manufacture(Subject("o/r", "a"*40, "b"*64, 1), KineticsModel(1, "c"*64, "CALIBRATED"), "PARTIAL_ALIVE", Capability(20, 20, Fraction(1), .8, Fraction(3,4), "CAPABLE"), EffectiveEpisodes(20,20,20,20,Fraction(1)))
        self.assertEqual(replay(receipt), "REPLAY_MATCH")
        receipt["body"]["standing"] = "ALIVE"
        with self.assertRaisesRegex(Refused, "RECEIPT_MISMATCH"):
            replay(receipt)
