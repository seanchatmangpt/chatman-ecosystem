import unittest
from fractions import Fraction
from scripts.develop_train.kantorovich_certificate_realization import *
from test_identity_admission import CERT, observation

class IndependenceCalibration(unittest.TestCase):
    def test_independence_and_currentness(self):
        obs = [observation(i) for i in range(11)]
        self.assertTrue(witness(obs).admitted)
        cal = calibrate(CERT, obs)
        self.assertTrue(cal.admitted())
        self.assertEqual(current([cal]).digest, cal.digest)

    def test_split_current_refuses(self):
        a = Calibration(8, "a"*64, 11, Fraction(0), Fraction(0), Fraction(0), Fraction(0))
        b = Calibration(8, "b"*64, 11, Fraction(0), Fraction(0), Fraction(0), Fraction(0))
        with self.assertRaises(Refused):
            current([a,b])

if __name__ == "__main__": unittest.main()
