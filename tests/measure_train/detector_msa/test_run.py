import unittest
from datetime import datetime, timezone, timedelta
from scripts.measure_train.detector_msa.case import DetectorCase
from scripts.measure_train.detector_msa.policy import DetectorPolicy
from scripts.measure_train.detector_msa.run import DetectorRun, admit_run
from scripts.measure_train.detector_msa.subject import Refused

class DetectorRunCourt(unittest.TestCase):
    def test_pretransition_alarm_refuses(self):
        start = datetime.now(timezone.utc)
        case = DetectorCase("case", "source", start, start + timedelta(seconds=10), start + timedelta(seconds=5))
        policy = DetectorPolicy("det", "WINDOW_L1", 1, ())
        run = DetectorRun("case", policy.fingerprint, start + timedelta(seconds=10), start + timedelta(seconds=2), "evidence")
        with self.assertRaises(Refused):
            admit_run(case, policy, run)
