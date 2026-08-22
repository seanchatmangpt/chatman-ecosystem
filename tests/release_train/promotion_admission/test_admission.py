import unittest
from scripts.release_train.promotion_admission.subject import Subject
from scripts.release_train.promotion_admission.evidence import Axis,Outcome
from scripts.release_train.promotion_admission.requirements import ReleaseProfile
from scripts.release_train.promotion_admission.admission import admit_subject
class T(unittest.TestCase):
    def test_broad_failure_dominates_focused_green(self):
        s=Subject("o/r","a"*40); p=ReleaseProfile("r",frozenset({Axis.FOCUSED,Axis.REPOSITORY}))
        r=admit_subject(s,{Axis.FOCUSED:Outcome.PASS,Axis.REPOSITORY:Outcome.FAIL},p)
        self.assertFalse(r.admitted); self.assertIn("FAILED_AXES:REPOSITORY",r.reasons)
if __name__=="__main__": unittest.main()
