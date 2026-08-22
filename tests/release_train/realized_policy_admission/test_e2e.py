import unittest
from scripts.release_train.realized_policy_admission.subject import Subject
from scripts.release_train.realized_policy_admission.policy import Policy
from scripts.release_train.realized_policy_admission.frontier import PolicyFrontier
from scripts.release_train.realized_policy_admission.admission import StrategyEvidence
from scripts.release_train.realized_policy_admission.moments import Moments
from scripts.release_train.realized_policy_admission.drift import DriftState
from scripts.release_train.realized_policy_admission.dependency import DependencyGraph
from scripts.release_train.realized_policy_admission.qualification import qualify
from scripts.release_train.realized_policy_admission.receipt import replay
class T(unittest.TestCase):
    def test_release_owner_policy_admission(self):
        subject=Subject("seanchatmangpt/chatman-ecosystem","a"*40)
        p=Policy(7,3,.25,1.5,1.5,.5)
        f=PolicyFrontier(7,p.digest,"c"*64)
        ev=StrategyEvidence(4,.0,1,1,Moments(4,.8,.04),DriftState())
        evidence={s:ev for s in ("MAX_INFORMATION_GAIN","MAX_INFORMATION_PER_COST","MIN_EXPECTED_ENTROPY")}
        metrics={"MAX_INFORMATION_GAIN":dict(lower_utility=.7,realized_gain=.8,cost_ratio=1,expected_entropy=.4),"MAX_INFORMATION_PER_COST":dict(lower_utility=.7,realized_gain=.75,cost_ratio=.5,expected_entropy=.4),"MIN_EXPECTED_ENTROPY":dict(lower_utility=.7,realized_gain=.7,cost_ratio=1,expected_entropy=.2)}
        q=qualify(subject,p,f,evidence,metrics,DependencyGraph({"release":("core",)},{"core":"PARTIAL_ALIVE"}),"release")
        self.assertEqual(q.selected_strategy,"MAX_INFORMATION_PER_COST")
        self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertEqual(q.phases,("VERIFY","CONSTRUCT"))
        self.assertTrue(replay(q.receipt)); self.assertFalse(q.actuation_performed)
