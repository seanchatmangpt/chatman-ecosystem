import unittest
from scripts.release_train.provenance_reconciliation.model import ExactSubject, Refused
from scripts.release_train.provenance_reconciliation.provenance import EvidenceRecord
from scripts.release_train.provenance_reconciliation.reconcile import reconcile_repo
from tests.release_train.provenance_reconciliation.helpers import SUBJECT_A,DIGEST

class ReconcileCourt(unittest.TestCase):
    def test_newest_subject_supersedes(self):
        newer=ExactSubject(SUBJECT_A.repo,"c"*40)
        rows=[EvidenceRecord("old",SUBJECT_A,"receipt","2026-08-22T08:00:00Z","https://github.com/a/b",DIGEST),EvidenceRecord("new",newer,"receipt","2026-08-22T09:00:00Z","https://github.com/a/b",DIGEST)]
        result=reconcile_repo(rows); self.assertEqual(newer,result.current_subject); self.assertEqual(("old",),result.superseded_ids)
    def test_same_time_conflict_refused(self):
        other=ExactSubject(SUBJECT_A.repo,"c"*40); t="2026-08-22T09:00:00Z"
        rows=[EvidenceRecord("a",SUBJECT_A,"receipt",t,"https://github.com/a/b",DIGEST),EvidenceRecord("b",other,"receipt",t,"https://github.com/a/b",DIGEST)]
        with self.assertRaisesRegex(Refused,"CONFLICTING_CURRENT_SUBJECT"): reconcile_repo(rows)
if __name__ == "__main__": unittest.main()
