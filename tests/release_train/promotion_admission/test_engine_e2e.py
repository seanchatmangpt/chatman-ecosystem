import unittest
from datetime import datetime, timezone
from scripts.release_train.promotion_admission.subject import Subject
from scripts.release_train.promotion_admission.evidence import Axis,Outcome,Evidence
from scripts.release_train.promotion_admission.requirements import ReleaseProfile
from scripts.release_train.promotion_admission.candidate import PromotionCandidate
from scripts.release_train.promotion_admission.dependency import DependencyGraph
from scripts.release_train.promotion_admission.engine import manufacture_promotion
from scripts.release_train.promotion_admission.receipt import replay_receipt
class T(unittest.TestCase):
    def setUp(self):
        self.dep=Subject("seanchatmangpt/gymact","7ce400e878c1da9b7dc46a81072563ec76ef01f4")
        self.root=Subject("seanchatmangpt/chatman-ecosystem","e41600a039977a12395aa565f1db736d6350bde3")
        self.now=datetime.now(timezone.utc); self.p=ReleaseProfile("promotion",frozenset({Axis.FOCUSED,Axis.REPOSITORY}))
        self.c=[PromotionCandidate("closure",self.root,90,100,100,10)]
        self.g=DependencyGraph({self.root:frozenset({self.dep})})
    def ev(self,s,repo_out):
        return [Evidence(s,Axis.FOCUSED,Outcome.PASS,self.now,"focused"),Evidence(s,Axis.REPOSITORY,repo_out,self.now,"repo")]
    def test_mixed_dependency_blocks_without_collapsing_subject(self):
        r=manufacture_promotion(self.c,self.g,{self.root:self.ev(self.root,Outcome.PASS),self.dep:self.ev(self.dep,Outcome.FAIL)},self.p,"e"*40)
        self.assertEqual(r.standing,"BLOCKED"); self.assertEqual(r.plan,()); self.assertTrue(replay_receipt(r.receipt)); self.assertFalse(r.receipt["body"]["actuation_performed"])
    def test_full_closure_manufactures_replayable_construct_plan(self):
        r=manufacture_promotion(self.c,self.g,{self.root:self.ev(self.root,Outcome.PASS),self.dep:self.ev(self.dep,Outcome.PASS)},self.p,"e"*40)
        self.assertEqual(r.standing,"PARTIAL_ALIVE"); self.assertEqual(len(r.plan),4); self.assertTrue(replay_receipt(r.receipt)); self.assertNotIn("DO",{p.phase for p in r.plan})
if __name__=="__main__": unittest.main()
