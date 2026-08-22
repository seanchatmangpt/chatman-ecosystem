import unittest
from scripts.release_train.window import ObservationWindow, WindowRefusal

class WindowTests(unittest.TestCase):
    def test_half_open_window(self):
        w = ObservationWindow.admit("2026-08-22T03:00:00Z", "2026-08-22T05:00:00Z")
        self.assertTrue(w.contains("2026-08-22T03:00:00Z"))
        self.assertFalse(w.contains("2026-08-22T05:00:00Z"))

    def test_refuses_reverse_window(self):
        with self.assertRaisesRegex(WindowRefusal, "INVALID_OBSERVATION_WINDOW"):
            ObservationWindow.admit("2026-08-22T05:00:00Z", "2026-08-22T03:00:00Z")
