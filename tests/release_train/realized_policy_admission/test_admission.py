import unittest
from scripts.release_train.realized_policy_admission.policy import Policy
from scripts.release_train.realized_policy_admission.admission import StrategyEvidence,admit_evidence
from scripts.release_train.realized_policy_admission.moments import Moments
from scripts.release_train.realized_policy_admission.drift import DriftState
class T(unittest.TestCase):
    def test_limits(self):
        p=Policy(1,3,.2,1.5,1.5,.5)
        good=StrategyEvidence(3,.1,1.1,1.1,Moments(3,1,0),DriftState())
        self.assertIs(admit_evidence(good,p),good)
        with self.assertRaisesRegex(ValueError,"UNDER_SUPPORTED"): admit_evidence(StrategyEvidence(2,.1,1,1,Moments(),DriftState()),p)
