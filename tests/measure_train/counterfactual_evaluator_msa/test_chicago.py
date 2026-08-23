import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.counterfactual_evaluator_msa.subject import Subject
from scripts.measure_train.counterfactual_evaluator_msa.estimator import EstimatorIdentity
from scripts.measure_train.counterfactual_evaluator_msa.case import EvaluationCase
from scripts.measure_train.counterfactual_evaluator_msa.independence import IndependenceProof
from scripts.measure_train.counterfactual_evaluator_msa.qualify import qualify
from scripts.measure_train.counterfactual_evaluator_msa.replay import replay
class T(unittest.TestCase):
 def test_independent_current_ope_estimators_are_bounded(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40)
  a=EstimatorIdentity("ips","IPS","1"*64); b=EstimatorIdentity("dr","DOUBLY_ROBUST","2"*64,"3"*64)
  cs=[]
  for i,t in enumerate([Fraction(2,5),Fraction(1,2),Fraction(3,5)]):
   cs.append(EvaluationCase(s,a,f"a{i}",t,t+Fraction(1,100),Fraction(1,2),Fraction(1,2),now))
   cs.append(EvaluationCase(s,b,f"b{i}",t,t-Fraction(1,100),Fraction(1,2),Fraction(1,2),now))
  specs=[("ips",1,"4"*64,a,[Fraction(49,100),Fraction(51,100)]),("dr",1,"5"*64,b,[Fraction(49,100),Fraction(51,100)])]
  q=qualify(s,cs,specs,[IndependenceProof("ips","dr","independent-runtime-and-model")],now)
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
