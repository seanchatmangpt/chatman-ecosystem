import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.outcome_capital_transport_msa.subject import Subject
from scripts.measure_train.outcome_capital_transport_msa.observation import OutcomeObservation,METHODS
from scripts.measure_train.outcome_capital_transport_msa.qualify import qualify
from scripts.measure_train.outcome_capital_transport_msa.failure_worlds import REQUIRED
from scripts.measure_train.outcome_capital_transport_msa.replay import replay
class T(unittest.TestCase):
 def test_full_synthetic_evidence_caps_positive_and_red_dominates(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc)
  rows=[]; i=0
  for method in sorted(METHODS):
   for j in range(5):
    rows.append(OutcomeObservation(s,f"{i}-{j}",method,f"engine{j%2}",f"region{j%2}",f"root{j}",1,Fraction(1),Fraction(0),"INDEPENDENT","INDEPENDENT",now))
   i+=1
  q=qualify(s,rows,now,correspondence=True,failure_worlds=REQUIRED)
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  red=qualify(s,rows,now,dependency_states=("BUILD_BROKEN",),correspondence=True,failure_worlds=REQUIRED)
  self.assertEqual(red["standing"],"BUILD_BROKEN")
