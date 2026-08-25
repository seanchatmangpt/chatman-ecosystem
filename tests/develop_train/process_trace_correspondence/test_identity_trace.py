import unittest
from scripts.develop_train.process_trace_correspondence import *
class T(unittest.TestCase):
 def test_identity_and_digest(self):
  with self.assertRaises(Refused): Subject("x@y")
  s=Subject("o/r@"+"a"*40); t=Trace(s,"beam",(Event("A","1"),)); self.assertEqual(t.digest,t.digest)
