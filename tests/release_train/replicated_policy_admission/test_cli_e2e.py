import unittest,json
from fixtures import SHA,POL,FRONT,NOW
from scripts.release_train.replicated_policy_admission.cli import manufacture
class TestE2E(unittest.TestCase):
    def test_deterministic_release_qualification(self):
        p={'repo':'seanchatmangpt/chatman-ecosystem','sha':SHA,'generation':7,'policy_digest':POL,'frontier_digest':FRONT,'not_before':'2026-08-23T00:00:00+00:00','expires_at':'2026-08-23T01:00:00+00:00','at':NOW.isoformat(),'replicas':[{'id':'a','generation':7,'policy_digest':POL,'frontier_digest':FRONT,'clock':{'a':1}},{'id':'b','generation':7,'policy_digest':POL,'frontier_digest':FRONT,'clock':{'a':1,'b':1}},{'id':'c','generation':7,'policy_digest':POL,'frontier_digest':FRONT,'clock':{'a':1,'b':1,'c':1}}],'edges':[['policy','release']],'standing':[['policy','PARTIAL_ALIVE'],['release','PARTIAL_ALIVE']]}
        a=manufacture(p); b=manufacture(json.loads(json.dumps(p))); self.assertEqual(a,b); self.assertEqual(a['standing'],'PARTIAL_ALIVE'); self.assertFalse(a['receipt']['actuation_performed'])
