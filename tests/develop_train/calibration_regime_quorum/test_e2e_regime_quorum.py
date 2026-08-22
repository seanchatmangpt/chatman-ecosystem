import unittest
from datetime import datetime,timedelta,timezone
from scripts.develop_train.calibration_regime_quorum.admission import RecoveryWitness
from scripts.develop_train.calibration_regime_quorum.authority_receipt import replay
from scripts.develop_train.calibration_regime_quorum.calibration import fit_model
from scripts.develop_train.calibration_regime_quorum.engine import qualify
from scripts.develop_train.calibration_regime_quorum.frontier import build_frontier
from scripts.develop_train.calibration_regime_quorum.independence import EvidenceSource,IndependenceProof
from scripts.develop_train.calibration_regime_quorum.persistence import PersistenceNeed
from scripts.develop_train.calibration_regime_quorum.regime import CalibrationRegime
from scripts.develop_train.calibration_regime_quorum.subject import Refusal,Subject
from scripts.develop_train.calibration_regime_quorum.trials import CalibrationTrial
def strong_model(source,now):
    pairs=[(1,1)]*6+[(0,0)]*6; rows=tuple(CalibrationTrial(source,t,p,now-timedelta(minutes=30-i)) for i,(t,p) in enumerate(pairs)); return fit_model(rows,source_id=source)
class E2ERegimeQuorumCourt(unittest.TestCase):
    def test_stable_independent_quorum_then_regime_move_refuses_historical_witness(self):
        now=datetime.now(timezone.utc); subject=Subject("owner/repo","f"*40); ma,mb=strong_model("a",now),strong_model("b",now); fa=build_frontier((CalibrationRegime("a",4,"STABLE",ma,now),)); fb=build_frontier((CalibrationRegime("b",7,"STABLE",mb,now),)); sa=EvidenceSource("a","p1","r1","x1","f1"); sb=EvidenceSource("b","p2","r2","x2","f2"); proof=IndependenceProof(sa.fingerprint,sb.fingerprint,True); wa=RecoveryWitness(subject,"a","PASS",now,4); wb=RecoveryWitness(subject,"b","PASS",now,7)
        q=qualify(subject=subject,witnesses=(wa,wb),frontiers={"a":fa,"b":fb},sources={"a":sa,"b":sb},proofs=(proof,),dependency_standings={},now=now,persistence_need=PersistenceNeed(transactional=True)); self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertEqual(q.independent_clusters,2); self.assertEqual(q.receipt.store,"SQLITE"); self.assertTrue(replay(q.receipt,q.receipt.digest())); self.assertFalse(q.receipt.actuation_performed)
        moved=build_frontier((CalibrationRegime("a",5,"DRIFT",ma,now+timedelta(seconds=1)),))
        with self.assertRaisesRegex(Refusal,"STALE_CALIBRATION_REGIME|CALIBRATION_DRIFTED"): qualify(subject=subject,witnesses=(wa,wb),frontiers={"a":moved,"b":fb},sources={"a":sa,"b":sb},proofs=(proof,),dependency_standings={},now=now+timedelta(seconds=1))
if __name__=="__main__": unittest.main()
