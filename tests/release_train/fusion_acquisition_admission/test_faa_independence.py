import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from scripts.release_train.fusion_acquisition_admission.subject import Subject
from scripts.release_train.fusion_acquisition_admission.sensor import SensorIdentity
from scripts.release_train.fusion_acquisition_admission.independence import IndependenceProof,maximum_independent_subset
from scripts.release_train.fusion_acquisition_admission.errors import Refused
class TestIndependence(unittest.TestCase):
    def test_explicit_graph(self):
        s=Subject("o/r@"+"c"*40); a=SensorIdentity(s,"a","fa","da",1,"1"*64); b=SensorIdentity(s,"b","fb","db",1,"2"*64); p=IndependenceProof(a,b,"p"); self.assertEqual(maximum_independent_subset([a,b],[p]),("a","b")); bad=SensorIdentity(s,"c","fa","dc",1,"3"*64)
        with self.assertRaises(Refused): IndependenceProof(a,bad,"x")
