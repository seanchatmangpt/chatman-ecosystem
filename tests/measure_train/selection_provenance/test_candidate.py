import unittest
from datetime import datetime, timezone
from scripts.measure_train.selection_provenance.subject import Subject, Refused
from scripts.measure_train.selection_provenance.candidate import CutCandidate

class TestCandidate(unittest.TestCase):
    def test_candidate_identity_and_generation(self):
        c = CutCandidate("1"*64, Subject("o/r","a"*40), "2"*64, 3, datetime.now(timezone.utc), True)
        self.assertEqual(c.generation, 3)
        with self.assertRaises(Refused):
            CutCandidate("1"*64, c.consumer, "2"*64, -1, datetime.now(timezone.utc), True)
