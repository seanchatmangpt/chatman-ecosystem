import unittest
from scripts.release_train.lineage import Predecessor, admit_predecessor, LineageRefusal
from scripts.release_train.subject import Subject

P=Predecessor("DMEDI_IMPLEMENT_25_COMMIT","https://github/pull/1","open",Subject.admit("o/r","a"*40),"o/r","b"*40)
class LineageTests(unittest.TestCase):
    def test_open_predecessor_is_exact_head(self):
        self.assertEqual(admit_predecessor("DMEDI_IMPLEMENT_25_COMMIT",P),"a"*40)
    def test_no_predecessor_bootstraps_root(self):
        self.assertEqual(admit_predecessor("DMEDI_IMPLEMENT_25_COMMIT",None),"LINEAGE_ROOT")
    def test_closed_unmerged_blocks(self):
        bad=Predecessor(P.key,P.pr_url,"closed",P.head,P.base_repo,P.base_sha)
        with self.assertRaisesRegex(LineageRefusal,"SCHEDULE_PR_LINEAGE"):
            admit_predecessor(P.key,bad)
