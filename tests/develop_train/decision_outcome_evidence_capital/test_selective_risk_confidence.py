from datetime import datetime, timezone, timedelta
import unittest
from scripts.develop_train.decision_outcome_evidence_capital import *
from scripts.develop_train.decision_outcome_evidence_capital.observation import OutcomeObservation

POL=Policy("p",3,"b"*64,LossMatrix(5.0,2.0,0.1))

def obs(propensity=.8):
    now=datetime.now(timezone.utc)-timedelta(minutes=1)
    out=[]
    for i,m in enumerate(sorted(REQUIRED)):
        truth=(i%2==0)
        d=Decision.INDEPENDENT if truth else Decision.DEPENDENT
        out.append(OutcomeObservation(f"o{i}",3,d,truth,.05,propensity,.01,m,"BEAM","us-east",f"r{i}",now+timedelta(seconds=i)))
    return out

class SelectiveRiskConfidence(unittest.TestCase):
    def test_propensity_and_bound(self):
        sample=obs()
        self.assertTrue(require_support(profile(sample)).admitted)
        self.assertLess(self_normalized(POL,sample),.1)
        self.assertGreaterEqual(empirical_bernstein([0,0,0,0,0,0]).upper,0)

    def test_bad_propensity_refuses(self):
        with self.assertRaises(Refused):
            require_support(profile(obs(.01)))

if __name__=="__main__": unittest.main()
