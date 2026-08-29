import json, subprocess, sys, unittest
from scripts.release_train.quorum_sensor_admission import ActionClass, Refused, qualify
from common import NOW, SUBJECT, clocks, deps, frontier, model, visibility, votes
class ChicagoCourt(unittest.TestCase):
 def test_calibrated_current_quorum_bounded_replayable(self):
  m=model(); q=qualify(subject=SUBJECT,model=m,frontier=frontier(m),visibility=visibility(),votes=votes(),clocks=clocks(),dependencies=deps(),now=NOW); self.assertEqual(q.receipt.standing,"PARTIAL_ALIVE"); self.assertFalse(q.receipt.actuation_performed); q.receipt.replay()
 def test_dependency_red_blocks_and_do_refuses(self):
  m=model(); q=qualify(subject=SUBJECT,model=m,frontier=frontier(m),visibility=visibility(),votes=votes(),clocks=clocks(),dependencies=deps("BUILD_BROKEN"),now=NOW); self.assertEqual(q.receipt.standing,"BLOCKED")
  with self.assertRaises(Refused): qualify(subject=SUBJECT,model=m,frontier=frontier(m),visibility=visibility(),votes=votes(),clocks=clocks(),dependencies=deps(),now=NOW,action=ActionClass.DO)
 def test_deterministic_cli(self):
  request=json.dumps({"subject":SUBJECT.canonical()}); cmd=[sys.executable,"-m","scripts.release_train.quorum_sensor_admission.cli"]; a=subprocess.run(cmd,input=request,text=True,capture_output=True); b=subprocess.run(cmd,input=request,text=True,capture_output=True); self.assertEqual((a.returncode,a.stdout),(0,b.stdout)); self.assertIn('"actuation_performed":false',a.stdout)
if __name__=="__main__": unittest.main()
