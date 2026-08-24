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
    def test_dynamics(self):
        t=Trajectory.build(observations()); self.assertGreaterEqual(descent_fraction(t),0.5); self.assertEqual(require_dwell(t,2),2); self.assertGreaterEqual(hitting_generation(t),0)
    def test_recurrence(self):
        x=observations(); a=x[0]; o=x[3]
        x[3]=ConvergenceObservation("r",3,a.semantic_digest,False,a.realized_blockers,a.realized_errors,a.realized_churn,o.methodology,o.engine,o.region,"rx",o.observed_at)
        self.assertTrue(recurrent(Trajectory.build(x)))
if __name__=="__main__": unittest.main()
