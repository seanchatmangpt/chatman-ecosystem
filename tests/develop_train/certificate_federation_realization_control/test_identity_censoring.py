from datetime import datetime, timezone, timedelta
import unittest
from scripts.develop_train.certificate_federation_realization_control import *
from scripts.develop_train.certificate_federation_realization_control.observation import Observation
SHA="a"*40
SUB=Subject.parse("seanchatmangpt/chatman-ecosystem@"+SHA)
CERT=Certificate(7,"b"*64,"c"*64)
METHODS=sorted(REQUIRED)
def observations():
    now=datetime.now(timezone.utc)-timedelta(minutes=1)
    return [Observation(f"o{i}",7,f"t{i%3}",f"impl{i%3}",f"model{i%3}",f"domain{i%3}",TransportState.RESOLVED,True,True,Relation.EXACT,10+i,m,"BEAM" if i%2==0 else "WASM","us-east" if i%2==0 else "eu-west",f"root-{i}",now+timedelta(seconds=i)) for i,m in enumerate(METHODS)]
class IdentityCensoring(unittest.TestCase):
    def test_exact_subject_and_censoring(self):
        with self.assertRaises(Refused): Subject.parse("x/y@bad")
        o=observations()[0]
        with self.assertRaises(Refused): Observation("x",7,"t","i","m","d",TransportState.TIMEOUT,True,True,Relation.EXACT,1,o.methodology,o.engine,o.region,o.evidence_root,o.observed_at)
    def test_census(self):
        self.assertEqual(census(observations()).resolved,len(METHODS))
if __name__=="__main__": unittest.main()
