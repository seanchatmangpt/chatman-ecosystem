import sys,unittest
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from scripts.release_train.fusion_acquisition_admission.subject import Subject
from scripts.release_train.fusion_acquisition_admission.sensor import SensorIdentity,Calibration
from scripts.release_train.fusion_acquisition_admission.observation import Observation
from scripts.release_train.fusion_acquisition_admission.independence import IndependenceProof
from scripts.release_train.fusion_acquisition_admission.acquisition import AcquisitionCandidate
from scripts.release_train.fusion_acquisition_admission.dependency import DependencyGraph
from scripts.release_train.fusion_acquisition_admission.qualification import qualify
class TestRefusalIntegration(unittest.TestCase):
    def test_ambiguity_constructs_next_evidence_only(self):
        s=Subject("seanchatmangpt/chatman-ecosystem@"+"a"*40); a=SensorIdentity(s,"s-a","family-a","domain-a",7,"1"*64); b=SensorIdentity(s,"s-b","family-b","domain-b",7,"2"*64); cs=[Calibration(a,20,"1/20","1/20","1/20"),Calibration(b,20,"1/20","1/20","1/20")]; now=datetime(2026,8,23,2,0,tzinfo=timezone.utc); obs=[Observation(s,a,"CURRENT","9/10",now,"e-a"),Observation(s,b,"STALE","9/10",now,"e-b")]; proofs=[IndependenceProof(a,b,"p")]; candidates=[AcquisitionCandidate("probe-info","19/20",1,8,15),AcquisitionCandidate("probe-independent","3/4",2,12,8)]; g=DependencyGraph(); g.add(s,standing="UNKNOWN"); q=qualify(subject=s,calibrations=cs,observations=obs,independence_proofs=proofs,candidates=candidates,dependencies=g,now=now); self.assertEqual(q.receipt.standing,"UNKNOWN"); self.assertIsNotNone(q.selected_acquisition); self.assertFalse(q.receipt.actuation_performed)
