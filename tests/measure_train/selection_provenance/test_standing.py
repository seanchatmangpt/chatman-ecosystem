import unittest
from datetime import datetime, timezone
from scripts.measure_train.selection_provenance.subject import Subject
from scripts.measure_train.selection_provenance.candidate import CutCandidate
from scripts.measure_train.selection_provenance.standing import standing

class TestStanding(unittest.TestCase):
    def test_measurement_green_is_bounded_and_dependency_failure_blocks(self):
        c=CutCandidate("1"*64,Subject("o/r","a"*40),"2"*64,1,datetime.now(timezone.utc),True)
        self.assertEqual(standing(c),"PARTIAL_ALIVE")
        self.assertEqual(standing(c,(),("BUILD_BROKEN",)),"BLOCKED")
