import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.replica_quorum_msa.subject import Subject,Refused
from scripts.measure_train.replica_quorum_msa.vector_clock import VectorClock
from scripts.measure_train.replica_quorum_msa.observation import ReplicaObservation
from scripts.measure_train.replica_quorum_msa.temporal import temporal_violations
from scripts.measure_train.replica_quorum_msa.frontier import CalibrationModel,current_frontier
class T(unittest.TestCase):
 def test_regression_and_divergence(self):
  s=Subject("o/r","a"*40); n=datetime.now(timezone.utc)
  a=ReplicaObservation(s,"r",2,"1"*64,VectorClock.from_dict({"r":2}),n,"a"*64)
  b=ReplicaObservation(s,"r",1,"2"*64,VectorClock.from_dict({"r":1}),n+timedelta(seconds=1),"b"*64)
  self.assertTrue(temporal_violations([a,b]))
  with self.assertRaises(Refused): current_frontier([CalibrationModel(2,"1"*64,"CALIBRATED"),CalibrationModel(2,"2"*64,"CALIBRATED")])
