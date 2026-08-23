import sys,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from scripts.release_train.fusion_acquisition_admission.subject import Subject
from scripts.release_train.fusion_acquisition_admission.sensor import SensorIdentity,Calibration
from scripts.release_train.fusion_acquisition_admission.observation import Observation
from scripts.release_train.fusion_acquisition_admission.errors import Refused
class TestSensorObservation(unittest.TestCase):
    def test_binding_and_time(self):
        s=Subject("o/r@"+"b"*40); si=SensorIdentity(s,"s1","f","d",1,"1"*64); Calibration(si,8,"1/10","1/10","1/10"); now=datetime.now(timezone.utc); o=Observation(s,si,"CURRENT","9/10",now,"e1"); o.require_current(now,10)
        with self.assertRaises(Refused): o.require_current(now+timedelta(seconds=11),10)
