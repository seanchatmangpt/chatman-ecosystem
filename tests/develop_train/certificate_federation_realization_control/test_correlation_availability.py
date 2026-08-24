from datetime import datetime, timezone, timedelta
import unittest
from scripts.develop_train.certificate_federation_realization_control import *
from scripts.develop_train.certificate_federation_realization_control.observation import Observation
METHODS=sorted(REQUIRED)
def observations():
    now=datetime.now(timezone.utc)-timedelta(minutes=1)
    return [Observation(f"o{i}",7,f"t{i%3}",f"impl{i%3}",f"model{i%3}",f"domain{i%3}",TransportState.RESOLVED,True,True,Relation.EXACT,10+i,m,"BEAM" if i%2==0 else "WASM","us-east" if i%2==0 else "eu-west",f"root-{i}",now+timedelta(seconds=i)) for i,m in enumerate(METHODS)]
class CorrelationAvailability(unittest.TestCase):
    def test_availability_and_independence(self):
        obs=observations(); self.assertGreater(wilson(obs).lower,0.5); self.assertLessEqual(abs(phi(obs[:4],obs[4:8]).phi),0.2)
    def test_correlated_refuses(self):
        base=observations()[0]; a=[]; b=[]
        for i in range(4):
            state=TransportState.TIMEOUT if i<2 else TransportState.RESOLVED; rel=Relation.CENSORED if state!=TransportState.RESOLVED else Relation.EXACT; realized=None if state!=TransportState.RESOLVED else True
            a.append(Observation(f"a{i}",7,f"a{i}","ia","ma","da",state,True,realized,rel,1,METHODS[i],"BEAM","us",f"ra{i}",base.observed_at+timedelta(seconds=i)))
            b.append(Observation(f"b{i}",7,f"b{i}","ib","mb","db",state,True,realized,rel,1,METHODS[i],"WASM","eu",f"rb{i}",base.observed_at+timedelta(seconds=i)))
        with self.assertRaises(Refused): require_independent(phi(a,b))
if __name__=="__main__": unittest.main()
