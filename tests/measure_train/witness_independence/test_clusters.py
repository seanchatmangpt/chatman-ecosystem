import unittest
from datetime import datetime,timezone
from scripts.measure_train.witness_independence.subject import Subject
from scripts.measure_train.witness_independence.source import EvidenceSource
from scripts.measure_train.witness_independence.observation import WitnessObservation
from scripts.measure_train.witness_independence.clusters import correlated_clusters
class T(unittest.TestCase):
 def test_duplicate_family_collapses(self):
  s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
  rows=[WitnessObservation(s,EvidenceSource("WORKFLOW","same",str(i),"","s"+str(i)),"REPOSITORY","PASS",str(i),now) for i in range(3)]
  self.assertEqual(len(correlated_clusters(rows)),1)
