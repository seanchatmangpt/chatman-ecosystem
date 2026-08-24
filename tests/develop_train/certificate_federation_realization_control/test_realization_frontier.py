from datetime import datetime, timezone, timedelta
import unittest
from scripts.develop_train.certificate_federation_realization_control import *
from scripts.develop_train.certificate_federation_realization_control.observation import Observation
METHODS=sorted(REQUIRED)
def observations():
    now=datetime.now(timezone.utc)-timedelta(minutes=1)
    return [Observation(f"o{i}",7,f"t{i%3}",f"impl{i%3}",f"model{i%3}",f"domain{i%3}",TransportState.RESOLVED,True,True,Relation.EXACT,10+i,m,"BEAM" if i%2==0 else "WASM","us-east" if i%2==0 else "eu-west",f"root-{i}",now+timedelta(seconds=i)) for i,m in enumerate(METHODS)]
class RealizationFrontier(unittest.TestCase):
    def test_directional_and_current(self):
        obs=observations(); self.assertEqual(evaluate(obs).false_current,0); cal=calibrate(obs,7); self.assertTrue(cal.admitted); self.assertEqual(current([cal]).generation,7)
    def test_split_current_refuses(self):
        a=Calibration(9,"a"*64,10,0.0,0.0,0.0); b=Calibration(9,"b"*64,10,0.0,0.0,0.0)
        with self.assertRaises(Refused): current([a,b])
if __name__=="__main__": unittest.main()
