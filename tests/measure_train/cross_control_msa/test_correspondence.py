import unittest
from datetime import datetime,timezone
from scripts.measure_train.cross_control_msa.subject import Subject
from scripts.measure_train.cross_control_msa.identity import ControlIdentity
from scripts.measure_train.cross_control_msa.observation import Observation
from scripts.measure_train.cross_control_msa.correspondence import result_correspondence
from scripts.measure_train.cross_control_msa.refusal import Refused
class T(unittest.TestCase):
 def test_divergence(self):
  s=Subject("o/r","a"*40,"b"*64,1);now=datetime.now(timezone.utc);fs=["SEARCH","SEMANTIC","DISTRIBUTED","SIMULATION"]
  rows=[Observation(s,ControlIdentity(f,str(i),chr(99+i)*64,chr(103+i)*64),str(i),"f"*64,now,"PASS") for i,f in enumerate(fs)]
  self.assertEqual(result_correspondence(rows),"f"*64)
  rows[-1]=Observation(s,rows[-1].control,"3","e"*64,now,"PASS")
  with self.assertRaises(Refused): result_correspondence(rows)
