import unittest
from datetime import datetime, timezone
from fractions import Fraction
from scripts.measure_train.certificate_federation_realization_msa.subject import Subject
from scripts.measure_train.certificate_federation_realization_msa.certificate import Certificate
from scripts.measure_train.certificate_federation_realization_msa.observation import Observation
from scripts.measure_train.certificate_federation_realization_msa.calibration import Calibration
from scripts.measure_train.certificate_federation_realization_msa.methodology import REQUIRED
from scripts.measure_train.certificate_federation_realization_msa.qualify import qualify
from scripts.measure_train.certificate_federation_realization_msa.replay import replay

class TestChicago(unittest.TestCase):
    def test_full_synthetic_federation_caps_at_partial_alive(self):
        now = datetime.now(timezone.utc)
        subject = Subject("o/r", "a"*40, "b"*64)
        certificate = Certificate(subject, 3, "c"*64)
        observations = [
            Observation(certificate, "t1", "d"*64, "e"*64, "x", "RESOLVED", "EXACT", "a"*40, 5, now),
            Observation(certificate, "t2", "f"*64, "1"*64, "y", "RESOLVED", "EXACT", "a"*40, 5, now),
        ]
        calibration = Calibration(20, Fraction(0), Fraction(0), "CALIBRATED")
        qualified = qualify(certificate, observations, calibration, ["t1", "t2"], REQUIRED, [], now, 0.0)
        self.assertEqual(qualified["standing"], "PARTIAL_ALIVE")
        self.assertEqual(qualified["coverage"], 1)
        self.assertEqual(replay(qualified["receipt"]), "REPLAY_MATCH")
        self.assertFalse(qualified["actuation_performed"])
        red = qualify(certificate, observations, calibration, ["t1", "t2"], REQUIRED, ["BUILD_BROKEN"], now, 0.0)
        self.assertEqual(red["standing"], "BUILD_BROKEN")
        self.assertIsNone(red["receipt"])
