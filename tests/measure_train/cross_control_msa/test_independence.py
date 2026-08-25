import unittest
from datetime import datetime,timezone
from scripts.measure_train.cross_control_msa.subject import Subject
from scripts.measure_train.cross_control_msa.identity import ControlIdentity
from scripts.measure_train.cross_control_msa.observation import Observation
from scripts.measure_train.cross_control_msa.independence import require_independence
from scripts.measure_train.cross_control_msa.capital import effective_capital
from scripts.measure_train.cross_control_msa.refusal import Refused
class T(unittest.TestCase):
 def test_duplicate_capital(self):
  s=Subject("o/r","a"*40,"b"*64,1);now=datetime.now(timezone.utc);rows=[Observation(s,ControlIdentity(f,"same","c"*64,"d"*64),f,"e"*64,now,"PASS") for f in ["SEARCH","SEMANTIC","DISTRIBUTED","SIMULATION"]]
  self.assertEqual(effective_capital(rows),1)
  with self.assertRaises(Refused): require_independence(rows)
