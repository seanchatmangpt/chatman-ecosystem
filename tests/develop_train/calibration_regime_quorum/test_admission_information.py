import unittest
from datetime import datetime,timedelta,timezone
from scripts.develop_train.calibration_regime_quorum.admission import RecoveryWitness,admit_witness
from scripts.develop_train.calibration_regime_quorum.calibration import fit_model
from scripts.develop_train.calibration_regime_quorum.frontier import build_frontier
from scripts.develop_train.calibration_regime_quorum.information import contribution
from scripts.develop_train.calibration_regime_quorum.regime import CalibrationRegime
from scripts.develop_train.calibration_regime_quorum.subject import Refusal,Subject
from scripts.develop_train.calibration_regime_quorum.trials import CalibrationTrial
class AdmissionInformationCourt(unittest.TestCase):
    def setUp(self):
        self.now=datetime.now(timezone.utc); pairs=[(1,1),(1,1),(0,0),(0,0),(1,1),(0,0)]; rows=tuple(CalibrationTrial("s",t,p,self.now-timedelta(seconds=10-i)) for i,(t,p) in enumerate(pairs)); self.model=fit_model(rows,source_id="s"); self.subject=Subject("owner/repo","a"*40)
    def test_current_stable_admits_and_unknown_is_zero_information(self):
        frontier=build_frontier((CalibrationRegime("s",2,"STABLE",self.model,self.now),)); w=RecoveryWitness(self.subject,"s","UNKNOWN",self.now,2); admit_witness(w,frontier,now=self.now); self.assertEqual(contribution(self.model,w).value,0)
    def test_stale_or_drifted_regime_refuses(self):
        frontier=build_frontier((CalibrationRegime("s",3,"DRIFT",self.model,self.now),)); stale=RecoveryWitness(self.subject,"s","PASS",self.now,2)
        with self.assertRaises(Refusal): admit_witness(stale,frontier,now=self.now)
        current=RecoveryWitness(self.subject,"s","PASS",self.now,3)
        with self.assertRaisesRegex(Refusal,"CALIBRATION_DRIFTED"): admit_witness(current,frontier,now=self.now)
if __name__=="__main__": unittest.main()
