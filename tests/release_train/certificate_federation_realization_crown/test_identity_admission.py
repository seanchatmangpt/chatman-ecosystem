import unittest
from scripts.release_train.certificate_federation_realization_crown import *
from scripts.release_train.certificate_federation_realization_crown.refusal import Refused

S=Subject("seanchatmangpt/chatman-ecosystem","1"*40,"certificate-federation")
C=Certificate(S,7,"a"*64,"b"*64)
def obs(t,state=TransportState.RESOLVED,relation=Relation.EXACT,impl=None):
    return Observation(S,7,t,impl or t,"m-"+t,"d-"+t,state,relation,True,True if state==TransportState.RESOLVED else None,
        "1"*40 if state==TransportState.RESOLVED else None,"a"*64 if state==TransportState.RESOLVED else None,"b"*64 if state==TransportState.RESOLVED else None)
class TestIdentityAdmission(unittest.TestCase):
    def test_exact_admission(self):
        self.assertEqual(2,len(admit_observations(C,[obs("a"),obs("b")])))
    def test_censored_semantic_claim_refuses(self):
        with self.assertRaises(Refused):
            Observation(S,7,"x","i","m","d",TransportState.TIMEOUT,Relation.CENSORED,True,True,"1"*40,"a"*64,"b"*64)
    def test_foreign_generation_refuses(self):
        o=obs("a")
        bad=Observation(S,8,o.transport_id,o.implementation,o.model,o.domain,o.state,o.relation,o.predicted_current,o.realized_current,o.observed_sha,o.semantic_digest,o.certificate_digest)
        with self.assertRaises(Refused): admit_observations(C,[bad])
