import unittest
from scripts.release_train.promotion_admission.subject import Subject
from scripts.release_train.promotion_admission.candidate import *
class T(unittest.TestCase):
    def test_frontier_is_reversible_and_deterministic(self):
        s=Subject("o/r","a"*40)
        cs=[PromotionCandidate("low",s,10,50,10,5),PromotionCandidate("high",s,90,90,90,10),PromotionCandidate("irreversible",s,100,0,100,0)]
        self.assertEqual([c.candidate_id for c in preserve_frontier(cs)],["high","low"])
if __name__=="__main__": unittest.main()
