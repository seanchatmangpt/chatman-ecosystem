import unittest
from datetime import datetime, timezone, timedelta
from fractions import Fraction
from scripts.measure_train.federation_convergence_kinetics_msa.subject import Subject
from scripts.measure_train.federation_convergence_kinetics_msa.observation import Observation
from scripts.measure_train.federation_convergence_kinetics_msa.episode import admit_episode
from scripts.measure_train.federation_convergence_kinetics_msa.refusal import Refused

class TestIdentityAdmission(unittest.TestCase):
    def test_torn_episode_refuses(self):
        subject = Subject("o/r", "a" * 40, "b" * 64, 1)
        now = datetime.now(timezone.utc)
        def row(step):
            return Observation(subject, "e", step, "ACTIVE", Fraction(1, 2), f"c{step}", "DISCOVERY", "E", "R", f"x{step}", now + timedelta(seconds=step))
        with self.assertRaisesRegex(Refused, "TORN_EPISODE"):
            admit_episode([row(0), row(2)])
