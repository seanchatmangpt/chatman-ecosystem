import unittest
from datetime import datetime,timedelta,timezone
from scripts.develop_train.calibration_regime_quorum.subject import Refusal,Subject
from scripts.develop_train.calibration_regime_quorum.trials import CalibrationTrial,admit_trials
class SubjectTrialCourt(unittest.TestCase):
    def test_exact_subject_and_trial_identity(self):
        s=Subject("owner/repo","a"*40); self.assertEqual(s.exact_id,f"owner/repo@{'a'*40}"); now=datetime.now(timezone.utc)
        t1=CalibrationTrial("source",True,True,now-timedelta(seconds=2)); t2=CalibrationTrial("source",True,True,now-timedelta(seconds=1)); rows=admit_trials([t2,t1],now=now); self.assertNotEqual(rows[0].trial_id,rows[1].trial_id)
    def test_inexact_duplicate_future_refuse(self):
        with self.assertRaises(Refusal): Subject("owner/repo","short")
        now=datetime.now(timezone.utc); t=CalibrationTrial("source",True,True,now)
        with self.assertRaisesRegex(Refusal,"DUPLICATE_CALIBRATION_TRIAL"): admit_trials([t,t],now=now)
        future=CalibrationTrial("source",True,True,now+timedelta(seconds=1))
        with self.assertRaisesRegex(Refusal,"FUTURE_CALIBRATION_TRIAL"): admit_trials([future],now=now)
if __name__=="__main__": unittest.main()
