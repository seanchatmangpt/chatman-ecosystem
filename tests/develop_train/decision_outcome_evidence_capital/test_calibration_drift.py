from datetime import datetime, timezone, timedelta
import unittest
from scripts.develop_train.decision_outcome_evidence_capital import *
from scripts.develop_train.decision_outcome_evidence_capital.observation import OutcomeObservation

class CalibrationDrift(unittest.TestCase):
    def test_mixed_truth_correct_decisions_calibrate(self):
        now=datetime.now(timezone.utc)-timedelta(minutes=1)
        obs=[]
        for i,truth in enumerate([True,False,True,False,True,False]):
            d=Decision.INDEPENDENT if truth else Decision.DEPENDENT
            obs.append(OutcomeObservation(str(i),3,d,truth,.05,.8,0,"discovery","BEAM","r","e"+str(i),now))
        c=calibrate(obs,3,"c"*64)
        self.assertTrue(c.admitted())
        self.assertEqual(current([c]).generation,3)
        s=Cusum(threshold=.5)
        for _ in range(3): s=s.update(.2)
        self.assertTrue(s.changed)

    def test_split_frontier_refuses(self):
        a=Calibration(10,.1,.1,4,"a"*64)
        b=Calibration(10,.1,.1,4,"b"*64)
        with self.assertRaises(Refused): current([a,b])

if __name__=="__main__": unittest.main()
