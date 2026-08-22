import unittest
from scripts.develop_train.calibration_regime_quorum.decision import decide
from scripts.develop_train.calibration_regime_quorum.information import InformationContribution
from scripts.develop_train.calibration_regime_quorum.standing import bounded_standing
class DecisionStandingCourt(unittest.TestCase):
    def test_positive_signal_is_bounded(self):
        d=decide((InformationContribution("a",1.5),InformationContribution("b",1.0))); s=bounded_standing(decision=d,independent_clusters=2,required_clusters=2,outcomes=("PASS","PASS"),dependency_standings={}); self.assertEqual(d.result,"ACCEPT_BOUNDED"); self.assertEqual(s.standing,"PARTIAL_ALIVE")
    def test_failure_and_dependency_red_dominate(self):
        d=decide((InformationContribution("a",3.0),)); self.assertEqual(bounded_standing(decision=d,independent_clusters=2,required_clusters=2,outcomes=("FAIL",),dependency_standings={}).standing,"BUILD_BROKEN"); blocked=bounded_standing(decision=d,independent_clusters=2,required_clusters=2,outcomes=("PASS",),dependency_standings={"upstream":"BUILD_BROKEN"}); self.assertEqual(blocked.standing,"BLOCKED")
if __name__=="__main__": unittest.main()
