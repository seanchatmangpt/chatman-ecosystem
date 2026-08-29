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
from scripts.release_train.fusion_acquisition_admission.authority import ActionClass
from scripts.release_train.fusion_acquisition_admission.errors import Refused
class TestChicago(unittest.TestCase):
    def world(self,broken=False):
        s=Subject("seanchatmangpt/chatman-ecosystem@"+"a"*40); a=SensorIdentity(s,"s-a","family-a","domain-a",7,"1"*64); b=SensorIdentity(s,"s-b","family-b","domain-b",7,"2"*64); cs=[Calibration(a,20,"1/20","1/20","1/20"),Calibration(b,20,"1/20","1/20","1/20")]; now=datetime(2026,8,23,2,0,tzinfo=timezone.utc); obs=[Observation(s,a,"CURRENT","9/10",now,"e-a"),Observation(s,b,"CURRENT","9/10",now,"e-b")]; proofs=[IndependenceProof(a,b,"p")]; cand=[AcquisitionCandidate("probe-info","19/20",1,8,15)]; g=DependencyGraph(); d=Subject("seanchatmangpt/gymact@"+"b"*40); g.add(d,standing="BUILD_BROKEN" if broken else "PARTIAL_ALIVE"); g.add(s,[d],standing="UNKNOWN"); return s,cs,obs,proofs,cand,g,now
    def test_release_paths(self):
        w=self.world(); q=qualify(subject=w[0],calibrations=w[1],observations=w[2],independence_proofs=w[3],candidates=w[4],dependencies=w[5],now=w[6]); self.assertEqual(q.receipt.standing,"PARTIAL_ALIVE"); self.assertIsNone(q.selected_acquisition); self.assertTrue(q.receipt.replay()); w=self.world(True); b=qualify(subject=w[0],calibrations=w[1],observations=w[2],independence_proofs=w[3],candidates=w[4],dependencies=w[5],now=w[6]); self.assertEqual(b.receipt.standing,"BLOCKED")
        with self.assertRaises(Refused): qualify(subject=w[0],calibrations=w[1],observations=w[2],independence_proofs=w[3],candidates=w[4],dependencies=w[5],now=w[6],action=ActionClass.DO)
