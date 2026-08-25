import sys, unittest
sys.path.insert(0,'scripts/release_train')
from risk_independence_admission import *
from risk_independence_admission.decision import Decision

class IdentityRisk(unittest.TestCase):
 def test_exact_identity_and_asymmetric_decision(self):
  s=Subject('seanchatmangpt/chatman-ecosystem','a'*40); self.assertIn('@',s.exact)
  r=decide(BetaEvidence(18,2),LossMatrix(9,2,2)); self.assertEqual(r.decision,Decision.INDEPENDENT)
 def test_invalid_sha_refuses(self):
  with self.assertRaises(Refused): Subject('a/b','short')
 def test_asymmetric_loss_changes_choice(self):
  e=BetaEvidence(6,4)
  self.assertNotEqual(decide(e,LossMatrix(20,1,20)).decision,decide(e,LossMatrix(1,20,20)).decision)
if __name__=='__main__':unittest.main()
