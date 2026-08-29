import unittest
from datetime import datetime, timezone
from scripts.release_train.process_transition_crown import (
    SubjectEpoch, RuntimeReceipt, WorkflowResult, State, EngineWitness, require_equivalent,
    RegionWitness, require_current, FailureWorld, REQUIRED_FAILURES, require_methods, REQUIRED_METHODS,
    Receipt, replay, compute
)

class ChicagoCrownTest(unittest.TestCase):
    def test_complete_bounded_transition_crown_path(self):
        s=SubjectEpoch("seanchatmangpt/chatman-ecosystem","a"*40,7,"sem")
        self.assertEqual(WorkflowResult(s.sha,"exact-head","success").state_for(s),State.ALIVE)
        self.assertEqual(RuntimeReceipt(s,"two-region inet_tls","inet_tls",True,"cert",0).admit(s).exit_status,0)
        require_equivalent((EngineWitness("BEAM","sem",("trace",),"t"),EngineWitness("WASM","sem",("trace",),"t")))
        now=datetime.now(timezone.utc)
        require_current((RegionWitness("h1","r1","sem","27","c1",now,True),RegionWitness("h2","r2","sem","27","c2",now,True)),now,60)
        FailureWorld(REQUIRED_FAILURES).require_complete()
        require_methods(set(REQUIRED_METHODS))
        states={k:State.ALIVE for k in ("methodology","powl","reactor","multi_engine","event_object_oracle","multi_region_tls","failure_world","brce","receipt_replay","exact_head")}
        states["broad_ci"]=State.UNKNOWN; states["repository_crown"]=State.UNKNOWN
        standing=compute(states)
        self.assertEqual(standing.state,State.UNKNOWN)
        leaf=Receipt(s,"qualification",(),{"standing":standing.state.value})
        self.assertEqual(replay((leaf,),leaf.digest()),leaf.digest())

if __name__=="__main__": unittest.main()
