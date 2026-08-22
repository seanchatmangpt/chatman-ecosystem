import unittest
from datetime import datetime, timezone
from scripts.release_train.promotion_admission.subject import Subject
from scripts.release_train.promotion_admission.evidence import *
class T(unittest.TestCase):
    def test_foreign_and_contradiction_refuse(self):
        a=Subject("o/a","a"*40); b=Subject("o/b","b"*40); now=datetime.now(timezone.utc)
        with self.assertRaisesRegex(EvidenceRefusal,"FOREIGN"): normalize_vector(a,[Evidence(b,Axis.FOCUSED,Outcome.PASS,now,"x")])
        rows=[Evidence(a,Axis.FOCUSED,Outcome.PASS,now,"x"),Evidence(a,Axis.FOCUSED,Outcome.FAIL,now,"y")]
        with self.assertRaisesRegex(EvidenceRefusal,"CONTRADICTORY"): normalize_vector(a,rows)
if __name__=="__main__": unittest.main()
