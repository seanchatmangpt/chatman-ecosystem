import unittest
from datetime import datetime, timezone, timedelta
from fractions import Fraction
from scripts.measure_train.federation_convergence_kinetics_msa.subject import Subject
from scripts.measure_train.federation_convergence_kinetics_msa.observation import Observation
from scripts.measure_train.federation_convergence_kinetics_msa.frontier import KineticsModel
from scripts.measure_train.federation_convergence_kinetics_msa.methodology import REQUIRED
from scripts.measure_train.federation_convergence_kinetics_msa.qualify import qualify
from scripts.measure_train.federation_convergence_kinetics_msa.replay import replay

class TestChicago(unittest.TestCase):
    def rows(self):
        subject = Subject("o/r", "a"*40, "b"*64, 7)
        now = datetime.now(timezone.utc)
        methods = sorted(REQUIRED)
        episodes = []
        for i in range(33):
            method = methods[i % len(methods)]
            episode_id = f"e{i}"
            episodes.append([
                Observation(subject, episode_id, 0, "ACTIVE", Fraction(19,20), f"c{i}", method, f"E{i%2}", f"R{i%2}", f"root{i}", now + timedelta(seconds=10*i)),
                Observation(subject, episode_id, 1, "FIXED", Fraction(19,20), f"c{i}", method, f"E{i%2}", f"R{i%2}", f"root{i}", now + timedelta(seconds=10*i+1)),
            ])
        return subject, episodes

    def test_clean_kinetics_caps_at_partial_alive_and_red_dependency_dominates(self):
        subject, episodes = self.rows()
        models = [KineticsModel(3, "d"*64, "CALIBRATED")]
        qualified = qualify(subject, episodes, models, 2, Fraction(3,4))
        self.assertEqual(qualified["standing"], "PARTIAL_ALIVE")
        self.assertEqual(replay(qualified["receipt"]), "REPLAY_MATCH")
        self.assertFalse(qualified["actuation_performed"])
        broken = qualify(subject, episodes, models, 2, Fraction(3,4), ["BUILD_BROKEN"])
        self.assertEqual(broken["standing"], "BUILD_BROKEN")
        self.assertIsNone(broken["receipt"])
