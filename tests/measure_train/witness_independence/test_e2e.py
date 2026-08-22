import unittest
from datetime import datetime,timezone
from scripts.measure_train.witness_independence.subject import Subject
from scripts.measure_train.witness_independence.source import EvidenceSource
from scripts.measure_train.witness_independence.observation import WitnessObservation
from scripts.measure_train.witness_independence.standing import IndependencePolicy
from scripts.measure_train.witness_independence.qualify import qualify
from scripts.measure_train.witness_independence.replay import replay
class T(unittest.TestCase):
 def test_duplicate_green_cannot_launder_independence(self):
  s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
  same=[WitnessObservation(s,EvidenceSource("WORKFLOW","gha",str(i),"","s"+str(i)),"REPOSITORY","PASS","same"+str(i),now) for i in range(3)]
  q=qualify(s,same,[],IndependencePolicy(2,"REPOSITORY"),now)
  self.assertEqual(q["standing"],"UNKNOWN")
  independent=WitnessObservation(s,EvidenceSource("RUNTIME","lab","x","","ind"),"REPOSITORY","PASS","ind",now)
  q2=qualify(s,same+[independent],[],IndependencePolicy(2,"REPOSITORY"),now)
  self.assertEqual(q2["standing"],"PARTIAL_ALIVE")
  self.assertFalse(q2["actuation_performed"]); self.assertEqual(replay(q2["receipt"]),"REPLAY_MATCH")
