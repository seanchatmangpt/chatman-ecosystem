import unittest
from scripts.release_train.promotion_epoch.barrier import qualify_barrier,REQUIRED
class T(unittest.TestCase):
 def test_alive(self): self.assertEqual(qualify_barrier({x:"PASS" for x in REQUIRED})[0],"ALIVE")
 def test_missing_unknown(self): self.assertEqual(qualify_barrier({"narrow":"PASS"})[0],"UNKNOWN")
 def test_failure_broken(self):
  r={x:"PASS" for x in REQUIRED}; r["e2e"]="FAIL"; self.assertEqual(qualify_barrier(r)[0],"BUILD_BROKEN")
