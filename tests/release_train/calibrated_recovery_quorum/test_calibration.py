import unittest
from datetime import datetime,timezone,timedelta
from scripts.release_train.calibrated_recovery_quorum.calibration import *
class T(unittest.TestCase):
 def test_fit_and_duplicate(self):
  t=datetime.now(timezone.utc); rows=[CalibrationTrial("s",True,True,t),CalibrationTrial("s",False,False,t+timedelta(seconds=1))]
  m=CalibrationModel.fit("s",rows); self.assertEqual(m.support,2)
  with self.assertRaises(Exception): CalibrationModel.fit("s",[rows[0],rows[0]])
