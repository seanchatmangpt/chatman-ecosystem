import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_transition_msa.subject import Subject,SubjectEpoch
from scripts.measure_train.process_intelligence_transition_msa.obligation import Obligation
from scripts.measure_train.process_intelligence_transition_msa.evidence import ObligationEvidence
from scripts.measure_train.process_intelligence_transition_msa.qualify import qualify_transition
from scripts.measure_train.process_intelligence_transition_msa.replay import replay

class T(unittest.TestCase):
    def test_live_shape_old_failure_discharged_broad_ci_stays_red(self):
        now=datetime.now(timezone.utc)
        old=SubjectEpoch(Subject("seanchatmangpt/ex4pm","7"*40),1)
        new=SubjectEpoch(Subject("seanchatmangpt/ex4pm","a"*40),2)
        obligations=[
            Obligation("reactor_chicago","REACTOR"),
            Obligation("cloud_qualification","CI"),
            Obligation("broad_ci","CI"),
            Obligation("runtime_replay","REPLAY"),
        ]
        before=[
            ObligationEvidence(old,"reactor_chicago","old-chicago","FAIL",now),
            ObligationEvidence(old,"cloud_qualification","old-cloud","FAIL",now),
            ObligationEvidence(old,"broad_ci","old-ci","FAIL",now),
        ]
        after=[
            ObligationEvidence(new,"reactor_chicago","new-chicago","PASS",now),
            ObligationEvidence(new,"cloud_qualification","new-cloud","PASS",now),
            ObligationEvidence(new,"broad_ci","new-ci","FAIL",now),
            ObligationEvidence(new,"runtime_replay","new-replay","PASS",now),
        ]
        q=qualify_transition(old,new,obligations,before,after,[("runtime_replay","reactor_chicago")],now)
        self.assertEqual({d.obligation_id for d in q["discharges"]},{"reactor_chicago","cloud_qualification","runtime_replay"})
        self.assertEqual(q["standing"],"BUILD_BROKEN")
        self.assertFalse(q["actuation_performed"])
        self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
