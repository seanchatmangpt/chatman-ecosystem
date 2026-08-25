import unittest
from fractions import Fraction
from scripts.release_train.transport_invariance_crown import Population, StressKind, StressWorld, Calibration, current_calibration, cusum, evaluate_worlds, Refused

class StressCalibrationCourt(unittest.TestCase):
    def test_stress_and_currentness_fail_closed(self):
        src=Population.from_mapping({'a':3,'b':2}); dst=Population.from_mapping({'a':1,'b':1})
        worlds=(StressWorld(StressKind.TARGET_SHIFT,'b',Fraction(1,10)), StressWorld(StressKind.SUPPORT_EROSION,'b',Fraction(1,10)))
        witness=evaluate_worlds(src,dst,worlds,0.2,0.5,1.0); self.assertTrue(witness.worlds)
        c=Calibration(4,30,0.03,0.2,'c'*64); self.assertEqual(current_calibration((c,),4,0.05),c)
        with self.assertRaisesRegex(Refused,'DIVERGENT_CURRENT_CALIBRATION'):
            current_calibration((c,Calibration(4,31,0.02,0.2,'d'*64)),4,0.05)
        self.assertTrue(cusum((0.01,0.2,0.3),0.05,0.0,0.15))
