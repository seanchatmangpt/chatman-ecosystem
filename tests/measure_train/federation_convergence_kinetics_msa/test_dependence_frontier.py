import unittest
from datetime import datetime, timezone
from fractions import Fraction
from scripts.measure_train.federation_convergence_kinetics_msa.subject import Subject
from scripts.measure_train.federation_convergence_kinetics_msa.observation import Observation
from scripts.measure_train.federation_convergence_kinetics_msa.episode import admit_episode
from scripts.measure_train.federation_convergence_kinetics_msa.dependence import effective_episodes
from scripts.measure_train.federation_convergence_kinetics_msa.frontier import KineticsModel, current
from scripts.measure_train.federation_convergence_kinetics_msa.refusal import Refused

class TestDependenceFrontier(unittest.TestCase):
    def test_duplicate_capital_and_split_current_refuse(self):
        subject = Subject("o/r", "a"*40, "b"*64, 1)
        now = datetime.now(timezone.utc)
        episodes = [admit_episode([Observation(subject, str(i), 0, "FIXED", Fraction(1), "same", "DISCOVERY", "E", "R", "same", now)]) for i in range(3)]
        self.assertEqual(effective_episodes(episodes).effective, 1)
        with self.assertRaisesRegex(Refused, "DIVERGENT_CURRENT_KINETICS_MODEL"):
            current([KineticsModel(1, "a"*64, "CALIBRATED"), KineticsModel(1, "b"*64, "CALIBRATED")])
