import sys,unittest
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from scripts.release_train.fusion_acquisition_admission.subject import Subject
from scripts.release_train.fusion_acquisition_admission.sensor import SensorIdentity,Calibration
from scripts.release_train.fusion_acquisition_admission.observation import Observation
from scripts.release_train.fusion_acquisition_admission.divergence import jensen_shannon
from scripts.release_train.fusion_acquisition_admission.fusion import robust_fuse
class TestDivergenceFusion(unittest.TestCase):
    def test_geometry_and_center(self):
        self.assertAlmostEqual(jensen_shannon([1,1,1],[1,1,1]),0.0); s=Subject("o/r@"+"d"*40); now=datetime.now(timezone.utc); ids=[SensorIdentity(s,x,f"f{x}",f"d{x}",1,str(i+1)*64) for i,x in enumerate("abc")]; cs=[Calibration(x,10,"1/20","1/20","1/20") for x in ids]; os=[Observation(s,x,"CURRENT","9/10",now,"e"+x.sensor_id) for x in ids]; self.assertEqual(robust_fuse(os,cs,("a","b","c")).verdict,"CURRENT")
