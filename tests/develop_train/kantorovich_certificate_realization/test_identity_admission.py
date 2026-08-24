import unittest
from datetime import datetime, timezone, timedelta
from fractions import Fraction
from scripts.develop_train.kantorovich_certificate_realization import *

SUB = Subject.parse("seanchatmangpt/chatman-ecosystem@" + "a" * 40 + "#" + "b" * 64)
CERT = Certificate("c" * 64, 7, Fraction(3, 2), Fraction(3, 2), Fraction(0), Fraction(0))

def observation(i=0, generation=7, digest="c"*64):
    return Observation(
        f"o{i}", digest, generation, Fraction(3,2), Fraction(1,1), Fraction(11,10),
        f"impl-{i%2}", f"model-{i%2}", f"root-{i%2}",
        sorted(REQUIRED)[i % len(REQUIRED)], "BEAM" if i%2==0 else "WASM",
        "us-east" if i%2==0 else "eu-west", datetime.now(timezone.utc)-timedelta(minutes=1)
    )

class IdentityAdmission(unittest.TestCase):
    def test_exact_subject_and_admission(self):
        self.assertTrue(SUB.key.endswith("b"*64))
        self.assertEqual(len(admit_observations(CERT, [observation(0)])), 1)
        with self.assertRaises(Refused):
            Subject.parse("seanchatmangpt/chatman-ecosystem@abc")

    def test_foreign_generation_refuses(self):
        with self.assertRaises(Refused):
            admit_observations(CERT, [observation(0, generation=8)])

if __name__ == "__main__": unittest.main()
