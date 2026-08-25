import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.evidence_calibration.subject import Subject
from scripts.measure_train.evidence_calibration.trial import CalibrationTrial
from scripts.measure_train.evidence_calibration.cluster import EvidenceCluster
from scripts.measure_train.evidence_calibration.admission import CurrentWitness
from scripts.measure_train.evidence_calibration.qualify import qualify
from scripts.measure_train.evidence_calibration.replay import replay
class T(unittest.TestCase):
 def test_calibrated_independent_quorum_only_bounded(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40)
  trials=[]
  for src in ("x","y"):
   for i in range(8):
    truth=i<6
    pred=truth if i!=6 else False
    trials.append(CalibrationTrial(src,f"{src}{i}",pred,truth,now-timedelta(days=1)))
  ws=[CurrentWitness(s,"a","x","PASS",now,"e1"),CurrentWitness(s,"b","y","PASS",now,"e2")]
  q=qualify(s,trials,ws,[EvidenceCluster("a",("x",)),EvidenceCluster("b",("y",))],now,
            min_trials=4,min_independent_clusters=2,accept_log_lr=1.0)
  self.assertEqual(q["standing"],"PARTIAL_ALIVE")
  self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
