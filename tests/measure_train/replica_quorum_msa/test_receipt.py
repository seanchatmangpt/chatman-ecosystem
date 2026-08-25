import unittest
from fractions import Fraction
from scripts.measure_train.replica_quorum_msa.subject import Subject,Refused
from scripts.measure_train.replica_quorum_msa.frontier import CalibrationModel
from scripts.measure_train.replica_quorum_msa.receipt import manufacture_receipt
from scripts.measure_train.replica_quorum_msa.replay import replay
class T(unittest.TestCase):
 def test_replay_and_authority_tamper(self):
  s=Subject("o/r","a"*40); m=CalibrationModel(1,"1"*64,"CALIBRATED")
  r=manufacture_receipt(s,{"state":"CURRENT_CANDIDATE","generation":1,"digest":"2"*64,"replicas":("a","b")},{"coverage":Fraction(2,3),"quorum_covered":True,"entropy_bits":1.0},m,"PARTIAL_ALIVE")
  self.assertEqual(replay(r),"REPLAY_MATCH"); self.assertFalse(r["body"]["actuation_performed"])
  r["body"]["authority"]="DO"
  with self.assertRaises(Refused): replay(r)
