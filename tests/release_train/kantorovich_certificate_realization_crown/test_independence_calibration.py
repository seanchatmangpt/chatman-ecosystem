import unittest
from fractions import Fraction
from scripts.release_train.kantorovich_certificate_realization_crown import Certificate,Observation,Refused
from scripts.release_train.kantorovich_certificate_realization_crown.independence import witness
from scripts.release_train.kantorovich_certificate_realization_crown.calibration import calibrate
from scripts.release_train.kantorovich_certificate_realization_crown.frontier import current
class T(unittest.TestCase):
    def obs(self,i,impl,model,root): return Observation(str(i),'b'*64,2,Fraction(1),Fraction(1),Fraction(1),impl,model,root,'discovery','BEAM','us','node')
    def test_independence_and_frontier(self):
        c=Certificate('b'*64,2,Fraction(1),Fraction(1)); xs=tuple(self.obs(i,'i'+str(i%2),'m'+str(i%2),'r'+str(i%2)) for i in range(4))
        self.assertEqual(witness(xs).roots,2); cal=calibrate(c,xs); self.assertEqual(current((cal,)).digest,cal.digest)
        with self.assertRaises(Refused): witness(tuple(self.obs(i,'i','m','r') for i in range(4)))
        alt=type(cal)(cal.generation,cal.support,cal.mae,cal.false_safe_rate,cal.digest+'x')
        with self.assertRaises(Refused): current((cal,alt))
if __name__=='__main__': unittest.main()
