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
    def test_full_path(self):
        subject=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40); obs=observations()
        q=qualify(subject,obs)
        self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertIsNotNone(q.receipt); self.assertEqual(replay(q.receipt,q.receipt.digest),"REPLAY_MATCH")
        red=qualify(subject,obs,{"root":["dep"],"dep":[]},{"dep":"BUILD_BROKEN"})
        self.assertEqual(red.standing,"BUILD_BROKEN"); self.assertIsNone(red.receipt)
if __name__=="__main__": unittest.main()
