import unittest
from datetime import datetime, timezone, timedelta
from fractions import Fraction
from scripts.measure_train.detector_msa.case import DetectorCase
from scripts.measure_train.detector_msa.policy import DetectorPolicy
from scripts.measure_train.detector_msa.run import DetectorRun
from scripts.measure_train.detector_msa.metrics import fit_metrics

class DetectorMetricsCourt(unittest.TestCase):
    def test_false_alarm_miss_and_delay_are_observable(self):
        start = datetime.now(timezone.utc)
        policy = DetectorPolicy("det", "WINDOW_L1", 1, ())
        cases = [
            DetectorCase("changed", "source", start, start + timedelta(seconds=10), start + timedelta(seconds=5)),
            DetectorCase("stable", "source", start, start + timedelta(seconds=10), None),
        ]
        runs = [
            DetectorRun("changed", policy.fingerprint, start + timedelta(seconds=10), start + timedelta(seconds=7), "e1"),
            DetectorRun("stable", policy.fingerprint, start + timedelta(seconds=10), None, "e2"),
        ]
        metrics = fit_metrics(cases, runs, policy)
        self.assertEqual(metrics.false_alarm_rate, Fraction(0))
        self.assertEqual(metrics.miss_rate, Fraction(0))
        self.assertEqual(metrics.median_delay_seconds, Fraction(2))
