import unittest
from scripts.develop_train.process_trace_correspondence import *
from scripts.develop_train.process_trace_correspondence.authority import admit
class T(unittest.TestCase):
 def test_do_refuses(self):
  self.assertEqual(admit(ActionClass.VERIFY),ActionClass.VERIFY)
  with self.assertRaises(Refused): admit(ActionClass.DO)
 def test_replay(self):
  r=Receipt("s","m","t",1,"PARTIAL_ALIVE",False); self.assertTrue(replay(r,r.body,r.digest)); bad=dict(r.body); bad["trace_digest"]="x"
  with self.assertRaises(Refused): replay(r,bad,r.digest)
