import unittest
from fractions import Fraction
from scripts.develop_train.sequential_acquisition.calibration import GainCalibration, admitted
from scripts.develop_train.sequential_acquisition.drift import CusumState, advance, drifted

class CalibrationDriftCourt(unittest.TestCase):
    def test_support_reliability_and_cusum_gate(self):
        self.assertTrue(admitted(GainCalibration("s",1,5,0.0,0.2,Fraction(9,10))))
        self.assertFalse(admitted(GainCalibration("s",1,1,0.0,0.2,Fraction(9,10))))
        state=CusumState()
        for _ in range(5): state=advance(state,0.5,allowance=0.1,threshold=1.0)
        self.assertTrue(drifted(state,1.0))
