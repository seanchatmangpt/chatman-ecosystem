import unittest
from scripts.release_train.provenance_reconciliation.model import Refused
from scripts.release_train.provenance_reconciliation.window import ObservationWindow

class WindowCourt(unittest.TestCase):
    def test_half_open_window(self):
        w=ObservationWindow("2026-08-22T07:38:39Z","2026-08-22T09:38:39Z")
        self.assertTrue(w.admits("2026-08-22T07:38:39Z")); self.assertFalse(w.admits("2026-08-22T09:38:39Z"))
    def test_outside_refused(self):
        with self.assertRaisesRegex(Refused,"OUTSIDE_OBSERVATION_WINDOW"): ObservationWindow("2026-08-22T08:00:00Z","2026-08-22T09:00:00Z").require("2026-08-22T07:59:59Z")
if __name__ == "__main__": unittest.main()
