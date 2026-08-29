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
    def test_calibration_capital(self):
        obs=observations(); c=calibrate(obs,len(obs)-1)
        self.assertTrue(c.admitted); self.assertTrue(require_capital(capital(obs)).admitted); self.assertEqual(current([c]).generation,len(obs)-1)
    def test_split(self):
        a=Calibration(2,5,0,0,"a"*64); b=Calibration(2,5,0,0,"b"*64)
        with self.assertRaises(Refused): current([a,b])
if __name__=="__main__": unittest.main()
