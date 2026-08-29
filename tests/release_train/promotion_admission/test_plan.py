import unittest
from scripts.release_train.promotion_admission.subject import Subject
from scripts.release_train.promotion_admission.plan import *
class T(unittest.TestCase):
    def test_plan_contains_no_do(self):
        s=Subject("o/r","a"*40); plan=build_plan((s,))
        self.assertEqual([p.phase for p in plan],["VERIFY","CONSTRUCT"])
        with self.assertRaisesRegex(PlanRefusal,"CONSEQUENTIAL"): PlanStep("DO",s,"x")
if __name__=="__main__": unittest.main()
