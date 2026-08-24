from datetime import datetime,timezone,timedelta
import unittest
from scripts.develop_train.federation_convergence_realization_control.api import *
METHODS=sorted(REQUIRED)
def observations():
    now=datetime.now(timezone.utc)-timedelta(minutes=2); out=[]; n=len(METHODS)
    for i,m in enumerate(METHODS):
        b=n-2-i if i<n-2 else 0
        out.append(ConvergenceObservation(f"o{i}",i,"b"*64,i>=n-2,b,0,0,m,"BEAM" if i%2==0 else "WASM","us-east" if i%2==0 else "eu-west",f"root-{i%3}",now+timedelta(seconds=i)))
    return out
class T(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(Trajectory.build(observations()).head.generation,len(METHODS)-1)
        with self.assertRaises(Refused): Subject.parse("bad")
    def test_torn(self):
        obs=observations(); obs.pop(3)
        with self.assertRaises(Refused): Trajectory.build(obs)
if __name__=="__main__": unittest.main()
