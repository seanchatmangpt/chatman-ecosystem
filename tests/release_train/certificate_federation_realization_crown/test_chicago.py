import unittest
from scripts.release_train.certificate_federation_realization_crown import *
from scripts.release_train.certificate_federation_realization_crown.failure_worlds import REQUIRED as WORLDS

class TestChicago(unittest.TestCase):
    def test_complete_bounded_chain_is_partial_alive_and_failure_dominates(self):
        s=Subject("seanchatmangpt/chatman-ecosystem","5"*40,"crown")
        c=Certificate(s,9,"a"*64,"b"*64)
        def o(t,p,r,impl,model,domain):
            return Observation(s,9,t,impl,model,domain,TransportState.RESOLVED,Relation.EXACT,p,r,"5"*40,"a"*64,"b"*64)
        observations=admit_observations(c,[
            o("api",True,True,"rest","model-a","github"),
            o("artifact",True,True,"artifact","model-b","actions"),
            o("mirror",False,True,"git","model-c","mirror"),
        ])
        require_transport_coverage(observations)
        err=evaluate(observations)
        model=calibrate(9,err)
        lower=wilson_lower(3,3)
        self.assertEqual(Recovery.OBSERVABILITY_RECOVERED,classify(Relation.CENSORED,Relation.EXACT))
        require_methodologies(REQUIRED_METHODOLOGIES); require_failure_worlds(WORLDS)
        q=qualify(s,model,(),lower,required_availability=0.2,max_false_current_rate=0.5)
        self.assertEqual("PARTIAL_ALIVE",q.standing); self.assertEqual("REPLAY_MATCH",replay(q.receipt))
        broken=qualify(s,model,("GymAct#118:BUILD_BROKEN",),lower)
        self.assertEqual("BUILD_BROKEN",broken.standing); self.assertIsNone(broken.receipt)
