from datetime import datetime, timezone, timedelta
import unittest
from scripts.develop_train.decision_outcome_evidence_capital import *
from scripts.develop_train.decision_outcome_evidence_capital.observation import OutcomeObservation

class Chicago(unittest.TestCase):
    def test_full_methodology_realization_and_failure_dominance(self):
        subject=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40)
        policy=Policy("p",3,"b"*64,LossMatrix(5.0,2.0,0.1))
        now=datetime.now(timezone.utc)-timedelta(minutes=1)
        observations=[]
        for i,m in enumerate(sorted(REQUIRED)):
            truth=(i%2==0)
            decision=Decision.INDEPENDENT if truth else Decision.DEPENDENT
            observations.append(OutcomeObservation(
                f"o{i}",3,decision,truth,.05,.8,.01,m,
                "BEAM" if i%2==0 else "WASM",
                "us-east" if i%2==0 else "eu-west",
                f"root-{i}",now+timedelta(seconds=i)))
        q=qualify(subject,policy,observations)
        self.assertEqual(q.standing,"PARTIAL_ALIVE")
        self.assertEqual(replay(q.receipt,q.receipt.digest),"REPLAY_MATCH")
        red=qualify(subject,policy,observations,dependencies=("BUILD_BROKEN",))
        self.assertEqual(red.standing,"BUILD_BROKEN")
        self.assertIsNone(red.receipt)

if __name__=="__main__": unittest.main()
