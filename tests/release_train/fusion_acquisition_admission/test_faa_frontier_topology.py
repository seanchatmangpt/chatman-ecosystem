import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from scripts.release_train.fusion_acquisition_admission.subject import Subject
from scripts.release_train.fusion_acquisition_admission.sensor import SensorIdentity,Calibration
from scripts.release_train.fusion_acquisition_admission.frontier import frontier,require_current
from scripts.release_train.fusion_acquisition_admission.errors import Refused
class TestFrontier(unittest.TestCase):
    def test_current_generation(self):
        s=Subject("o/r@"+"e"*40); a=Calibration(SensorIdentity(s,"a","fa","da",2,"1"*64),8,"1/10","1/10","1/10"); old=Calibration(SensorIdentity(s,"b","fb","db",1,"2"*64),8,"1/10","1/10","1/10"); f=frontier([a,old]); self.assertEqual(f.generation,2)
        with self.assertRaises(Refused): require_current(old,f)
