import unittest
from datetime import datetime, timezone, timedelta
from scripts.measure_train.detector_msa.case import DetectorCase
from scripts.measure_train.detector_msa.subject import Refused

class DetectorCaseCourt(unittest.TestCase):
    def test_half_open_transition_boundary(self):
        start = datetime(2026, 8, 22, tzinfo=timezone.utc)
        end = start + timedelta(seconds=10)
        with self.assertRaises(Refused):
            DetectorCase("case", "source", start, end, end)
