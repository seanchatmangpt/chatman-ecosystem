import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.cross_control_msa.subject import Subject
from scripts.measure_train.cross_control_msa.identity import ControlIdentity
from scripts.measure_train.cross_control_msa.observation import Observation
from scripts.measure_train.cross_control_msa.calibration import Calibration
from scripts.measure_train.cross_control_msa.qualify import qualify
from scripts.measure_train.cross_control_msa.replay import replay
class T(unittest.TestCase):
 def test_composition(self):
  now=datetime.now(timezone.utc);s=Subject("seanchatmangpt/ex4pm","a"*40,"b"*64,7);fs=["SEARCH","SEMANTIC","DISTRIBUTED","SIMULATION"]
  rows=[Observation(s,ControlIdentity(f,f"impl{i}",chr(99+i)*64,chr(103+i)*64),str(i),"f"*64,now,"PASS") for i,f in enumerate(fs)]
  q=qualify(s,rows,Calibration(20,Fraction(1,20),Fraction(1,20),"CALIBRATED"),now)
  self.assertEqual(q["standing"],"PARTIAL_ALIVE");self.assertEqual(q["effective_capital"],4);self.assertFalse(q["actuation_performed"]);self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
