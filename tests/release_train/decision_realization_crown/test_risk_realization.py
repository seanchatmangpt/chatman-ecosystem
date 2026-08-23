import unittest
from fractions import Fraction
from scripts.release_train.decision_realization_crown import *
from scripts.release_train.decision_realization_crown.loss import realized_loss
class T(unittest.TestCase):
  def setUp(self): self.p=DecisionPolicy("p",1,"b"*64,LossMatrix(9,2,1))
  def obs(self,d,t,prop=1): return Observation(str(d)+str(t)+str(prop),1,d,t,Fraction(1,10),prop,0,0,"discovery","BEAM","us","r")
  def test_asymmetry_and_propensity(self):
    fi=self.obs(Decision.INDEPENDENT,False,Fraction(1,2)); fd=self.obs(Decision.DEPENDENT,True,1)
    self.assertEqual(realized_loss(self.p,fi),9); self.assertEqual(realized_loss(self.p,fd),2)
    self.assertGreater(horvitz_thompson(self.p,[fi,fd]),self_normalized(self.p,[fi,fd]))
  def test_unobserved_regret_refuses(self):
    with self.assertRaises(Refused): observed_regret(self.p,self.obs(Decision.INDEPENDENT,False))
