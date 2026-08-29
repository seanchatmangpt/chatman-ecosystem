import unittest
from scripts.release_train.evidence import Evidence, EvidenceRefusal, standing
from scripts.release_train.window import ObservationWindow

W = ObservationWindow.admit("2026-08-22T03:00:00Z", "2026-08-22T05:00:00Z")
def row(status="success"):
    return Evidence.admit(key="ci", repo="seanchatmangpt/gymact", sha="a"*40,
        observed_at="2026-08-22T04:00:00Z", status=status, source="github-actions", window=W)

class EvidenceTests(unittest.TestCase):
    def test_standing_never_promotes_ci_to_alive(self):
        self.assertEqual(standing([row()]), "PARTIAL_ALIVE")
    def test_failure_dominates(self):
        self.assertEqual(standing([row(), row("failure")]), "BUILD_BROKEN")
    def test_pending_is_unknown(self):
        self.assertEqual(standing([row("queued")]), "UNKNOWN")
    def test_refuses_out_of_window(self):
        with self.assertRaisesRegex(EvidenceRefusal, "OUTSIDE_OBSERVATION_WINDOW"):
            Evidence.admit(key="x", repo="o/r", sha="a"*40, observed_at="2026-08-22T06:00:00Z",
                status="success", source="s", window=W)
