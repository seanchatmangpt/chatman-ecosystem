import unittest
from scripts.release_train.detector_consensus_recovery.admission import admit_votes
from scripts.release_train.detector_consensus_recovery.consensus import decide
from helpers import detector,generation,vote,proof
class Court(unittest.TestCase):
 def test_two_independent_are_required(self):
  a=detector("c","CUSUM","r1"); b=detector("e","EWMA","r2"); ga,gb=generation(a),generation(b); av=admit_votes([vote(a,ga,"STABLE"),vote(b,gb,"STABLE")],[ga,gb])
  self.assertEqual(decide(av,[proof(a,b)]).verdict,"STABLE_CONFIRMED"); self.assertEqual(decide(av,[]).verdict,"INSUFFICIENT")
 def test_same_family_has_no_ambient_independence(self):
  a=detector("c1","CUSUM","r1"); b=detector("c2","CUSUM","r2"); ga,gb=generation(a),generation(b); av=admit_votes([vote(a,ga,"DRIFT"),vote(b,gb,"DRIFT")],[ga,gb]); self.assertEqual(decide(av,[]).verdict,"INSUFFICIENT")
