import unittest
from scripts.release_train.provenance_reconciliation.authority import AuthorityContext
from scripts.release_train.provenance_reconciliation.dependency import DependencyEdge
from scripts.release_train.provenance_reconciliation.engine import manufacture
from scripts.release_train.provenance_reconciliation.receipt import replay
from scripts.release_train.provenance_reconciliation.window import ObservationWindow
from tests.release_train.provenance_reconciliation.helpers import SUBJECT_A,SUBJECT_B,records_for,claims_for

class EngineE2E(unittest.TestCase):
    def test_two_repo_dependency_closed_manufacture(self):
        records=records_for(SUBJECT_A)+records_for(SUBJECT_B); claims=claims_for(SUBJECT_A)+claims_for(SUBJECT_B)
        r=manufacture(predecessor_sha="f"*40,window=ObservationWindow("2026-08-22T08:00:00Z","2026-08-22T10:00:00Z"),records=records,evidence_edges=[],claims=claims,subjects=[SUBJECT_A,SUBJECT_B],dependencies=[DependencyEdge(SUBJECT_B,SUBJECT_A)],authority=AuthorityContext("schedule"))
        self.assertEqual((SUBJECT_B.coordinate,SUBJECT_A.coordinate),r.ordered_subjects); self.assertTrue(all(s.action in {"VERIFY","CONSTRUCT"} for s in r.steps)); replay(r.receipt)
if __name__ == "__main__": unittest.main()
