import unittest
from scripts.release_train.provenance_reconciliation.dependency import DependencyEdge, dependency_order
from scripts.release_train.provenance_reconciliation.model import Refused
from tests.release_train.provenance_reconciliation.helpers import SUBJECT_A,SUBJECT_B

class DependencyCourt(unittest.TestCase):
    def test_order(self): self.assertEqual([SUBJECT_B,SUBJECT_A],dependency_order([SUBJECT_A,SUBJECT_B],[DependencyEdge(SUBJECT_B,SUBJECT_A)]))
    def test_cycle_refused(self):
        with self.assertRaisesRegex(Refused,"DEPENDENCY_CYCLE"): dependency_order([SUBJECT_A,SUBJECT_B],[DependencyEdge(SUBJECT_A,SUBJECT_B),DependencyEdge(SUBJECT_B,SUBJECT_A)])
if __name__ == "__main__": unittest.main()
