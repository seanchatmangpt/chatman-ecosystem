import unittest
from datetime import datetime,timezone
from scripts.measure_train.provenance.subject import Subject
from scripts.measure_train.provenance.source import Source
from scripts.measure_train.provenance.claim import Claim
from scripts.measure_train.provenance.provenance import ProvenanceEdge
from scripts.measure_train.provenance.qualify import qualify
from scripts.measure_train.provenance.replay import replay
class T(unittest.TestCase):
 def test_full_non_actuating(self):
  s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
  a=Claim(s,Source("GITHUB_ACTION","run:1"),now,"PASS","run"); b=Claim(s,Source("RECEIPT","artifact:1"),now,"PASS","receipt")
  q=qualify(s,[a,b],[ProvenanceEdge("receipt","run","ATTESTS")])
  self.assertEqual(q["coverage"]["standing"],"PARTIAL_ALIVE")
  self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
