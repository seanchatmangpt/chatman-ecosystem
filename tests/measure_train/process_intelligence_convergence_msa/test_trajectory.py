import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.process_intelligence_convergence_msa.subject import Subject,Refused
from scripts.measure_train.process_intelligence_convergence_msa.epoch import ClosureEpoch
from scripts.measure_train.process_intelligence_convergence_msa.trajectory import admit_trajectory
class T(unittest.TestCase):
 def test_gap_refuses(self):
  now=datetime.now(timezone.utc)
  a=ClosureEpoch(Subject("o/r","a"*40,1),now,())
  b=ClosureEpoch(Subject("o/r","b"*40,3),now+timedelta(seconds=1),())
  with self.assertRaises(Refused): admit_trajectory([a,b])
