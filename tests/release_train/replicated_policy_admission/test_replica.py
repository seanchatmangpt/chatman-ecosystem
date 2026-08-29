import unittest
from scripts.release_train.replicated_policy_admission.replica import ReplicaPolicyState
from scripts.release_train.replicated_policy_admission.vector_clock import VectorClock
from scripts.release_train.replicated_policy_admission.refusal import Refused
from fixtures import subject,POL,FRONT
class TestReplica(unittest.TestCase):
    def test_digest_deterministic(self):
        a=ReplicaPolicyState('r1',subject(),1,POL,FRONT,VectorClock.from_dict({'r1':1})); self.assertEqual(a.digest,a.digest)
    def test_invalid_digest_refuses(self):
        with self.assertRaisesRegex(Refused,'INVALID_DIGEST'): ReplicaPolicyState('r',subject(),1,'x',FRONT,VectorClock.from_dict({'r':1}))
