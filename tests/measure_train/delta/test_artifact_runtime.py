import unittest
from scripts.measure_train.delta.artifact import ArtifactEvidence
from scripts.measure_train.delta.runtime import RuntimeEvidence
class T(unittest.TestCase):
 def test_artifact_binding_and_runtime_ceiling(self):
  a=ArtifactEvidence("x","a"*64,"b"*40); self.assertTrue(a.binds("b"*40)); self.assertEqual(RuntimeEvidence("b"*40,True,0,True).standing,"PARTIAL_ALIVE")
