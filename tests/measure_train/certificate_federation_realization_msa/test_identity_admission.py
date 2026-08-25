import unittest
from datetime import datetime, timezone
from scripts.measure_train.certificate_federation_realization_msa.subject import Subject, Refused
from scripts.measure_train.certificate_federation_realization_msa.certificate import Certificate
from scripts.measure_train.certificate_federation_realization_msa.observation import Observation
from scripts.measure_train.certificate_federation_realization_msa.admission import admit

class TestIdentityAdmission(unittest.TestCase):
    def test_censored_observation_cannot_claim_semantics(self):
        subject = Subject("o/r", "a"*40, "b"*64)
        certificate = Certificate(subject, 1, "c"*64)
        now = datetime.now(timezone.utc)
        row = Observation(certificate, "t", "d"*64, "e"*64, "x", "TIMEOUT", "CENSORED", None, 10, now)
        self.assertEqual(admit(certificate, [row], now), (row,))
        with self.assertRaises(Refused):
            Observation(certificate, "bad", "d"*64, "e"*64, "x", "TIMEOUT", "EXACT", "a"*40, 10, now)
