import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.replica_quorum_msa.subject import Subject
from scripts.measure_train.replica_quorum_msa.vector_clock import VectorClock
from scripts.measure_train.replica_quorum_msa.observation import ReplicaObservation
from scripts.measure_train.replica_quorum_msa.window import ObservationWindow
from scripts.measure_train.replica_quorum_msa.topology import ReplicaUniverse
from scripts.measure_train.replica_quorum_msa.frontier import CalibrationModel
from scripts.measure_train.replica_quorum_msa.qualify import qualify
from scripts.measure_train.replica_quorum_msa.replay import replay
class T(unittest.TestCase):
 def test_calibrated_quorum_is_bounded_and_partition_degrades(self):
  s=Subject("o/r","a"*40); n=datetime.now(timezone.utc); u=ReplicaUniverse.from_ids(["a","b","c"])
  def o(r,d="1"): return ReplicaObservation(s,r,3,d*64,VectorClock.from_dict({"a":3,"b":3}),n,r[0]*64)
  model=CalibrationModel(4,"9"*64,"CALIBRATED"); w=ObservationWindow(n-timedelta(seconds=1),n+timedelta(seconds=1))
  q=qualify(s,u,[o("a"),o("b")],w,[model])
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  degraded=qualify(s,u,[o("a")],w,[model]); self.assertEqual(degraded["standing"],"UNKNOWN")
