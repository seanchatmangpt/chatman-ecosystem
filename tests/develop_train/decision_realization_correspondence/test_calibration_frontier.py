import unittest
from fractions import Fraction

from scripts.develop_train.decision_realization_correspondence import Observation, RealizationModel, Refused, calibrate, current


class CalibrationFrontierCourt(unittest.TestCase):
    def test_calibration_and_split_currentness(self):
        obs = [
            Observation(str(i), 2, "INDEPENDENT", "INDEPENDENT", Fraction(), Fraction(1), Fraction(), "prediction", "BEAM", "us", f"r{i}")
            for i in range(4)
        ]
        calibration = calibrate(obs)
        self.assertTrue(calibration.admitted)
        with self.assertRaises(Refused):
            current([
                RealizationModel(3, "a" * 64, True, False),
                RealizationModel(3, "b" * 64, True, False),
            ])


if __name__ == "__main__":
    unittest.main()
