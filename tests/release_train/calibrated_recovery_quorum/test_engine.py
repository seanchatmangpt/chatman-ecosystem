import unittest
from datetime import datetime, timezone, timedelta
from scripts.release_train.calibrated_recovery_quorum.subject import Subject
from scripts.release_train.calibrated_recovery_quorum.source import EvidenceSource
from scripts.release_train.calibrated_recovery_quorum.witness import RecoveryWitness
from scripts.release_train.calibrated_recovery_quorum.calibration import CalibrationModel
from scripts.release_train.calibrated_recovery_quorum.independence import IndependenceProof
from scripts.release_train.calibrated_recovery_quorum.dependencies import DependencyGraph
from scripts.release_train.calibrated_recovery_quorum.persistence import PersistenceNeed
from scripts.release_train.calibrated_recovery_quorum.engine import qualify

class T(unittest.TestCase):
 def test_independent_calibrated_sources_are_bounded(self):
  now=datetime(2026,8,22,19,30,tzinfo=timezone.utc)
  subject=Subject("example/repo","1"*40)
  left=EvidenceSource("sensor-a","run-a","artifact-a","family-a")
  right=EvidenceSource("sensor-b","run-b","artifact-b","family-b")
  models=[CalibrationModel(left.fingerprint,8,7,0,1,0),CalibrationModel(right.fingerprint,8,7,0,1,0)]
  witnesses=[RecoveryWitness("attempt",left.fingerprint,"PASS",now-timedelta(seconds=2)),RecoveryWitness("attempt",right.fingerprint,"PASS",now-timedelta(seconds=1))]
  proofs=[IndependenceProof(left.fingerprint,right.fingerprint,True)]
  out=qualify(subject,"attempt",[left,right],witnesses,models,proofs,DependencyGraph({subject.exact:[]}),{},PersistenceNeed(transactional=True),now)
  self.assertEqual(out["standing"],"PARTIAL_ALIVE")
  self.assertEqual(out["store"],"SQLITE")
  self.assertTrue(out["replay"])
  self.assertFalse(out["receipt"].payload["actuation_performed"])

 def test_under_calibrated_source_stays_unknown(self):
  now=datetime(2026,8,22,19,30,tzinfo=timezone.utc)
  subject=Subject("example/repo","2"*40)
  source=EvidenceSource("sensor","run","artifact","family")
  model=CalibrationModel(source.fingerprint,2,2,0,0,0)
  witness=RecoveryWitness("attempt",source.fingerprint,"PASS",now-timedelta(seconds=1))
  out=qualify(subject,"attempt",[source],[witness],[model],[],DependencyGraph({subject.exact:[]}),{},PersistenceNeed(),now,required_clusters=1)
  self.assertEqual(out["standing"],"UNKNOWN")
