import unittest
from datetime import datetime, timezone, timedelta
from fractions import Fraction
from scripts.measure_train.federation_convergence_kinetics_msa.subject import Subject
from scripts.measure_train.federation_convergence_kinetics_msa.observation import Observation
from scripts.measure_train.federation_convergence_kinetics_msa.episode import admit_episode
from scripts.measure_train.federation_convergence_kinetics_msa.competing_risks import cumulative_incidence
from scripts.measure_train.federation_convergence_kinetics_msa.transition import transition_kernel
from scripts.measure_train.federation_convergence_kinetics_msa.absorption import absorption_probability

class TestCompetingAbsorption(unittest.TestCase):
    def test_fixed_and_regressed_do_not_collapse(self):
        subject = Subject("o/r", "a"*40, "b"*64, 1)
        now = datetime.now(timezone.utc)
        def episode(eid, terminal):
            return admit_episode([
                Observation(subject, eid, 0, "ACTIVE", Fraction(1,2), eid, "DISCOVERY", "E", "R", eid, now),
                Observation(subject, eid, 1, terminal, Fraction(1,2), eid, "DISCOVERY", "E", "R", eid, now + timedelta(seconds=1)),
            ])
        rows = [episode("a", "FIXED"), episode("b", "REGRESSED")]
        self.assertEqual(dict(cumulative_incidence(rows)[0][2])["FIXED"], Fraction(1,2))
        self.assertEqual(absorption_probability(transition_kernel(rows), horizon=1), Fraction(1,2))
