import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.replica_quorum_msa.subject import Subject
from scripts.measure_train.replica_quorum_msa.vector_clock import VectorClock
from scripts.measure_train.replica_quorum_msa.observation import ReplicaObservation
from scripts.measure_train.replica_quorum_msa.window import ObservationWindow,admit_window
class T(unittest.TestCase):
 def test_half_open_window(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40); c=VectorClock.from_dict({"r":1})
  a=ReplicaObservation(s,"r",1,"1"*64,c,now,"2"*64); b=ReplicaObservation(s,"x",1,"1"*64,c,now+timedelta(seconds=1),"3"*64)
  self.assertEqual(admit_window([a,b],ObservationWindow(now,now+timedelta(seconds=1))),(a,))
