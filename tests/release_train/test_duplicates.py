import unittest
from scripts.release_train.duplicates import reconcile, DuplicateRefusal
from scripts.release_train.evidence import Evidence
from scripts.release_train.window import ObservationWindow

W=ObservationWindow.admit("2026-08-22T03:00:00Z","2026-08-22T05:00:00Z")
def e(status="success"):
    return Evidence.admit(key="run-1",repo="o/r",sha="a"*40,observed_at="2026-08-22T04:00:00Z",
        status=status,source="actions",window=W)

class DuplicateTests(unittest.TestCase):
    def test_identical_duplicate_collapses(self):
        self.assertEqual(len(reconcile([e(),e()])),1)
    def test_conflict_refuses(self):
        with self.assertRaisesRegex(DuplicateRefusal,"CONFLICTING_DUPLICATE_EVIDENCE"):
            reconcile([e(),e("failure")])
