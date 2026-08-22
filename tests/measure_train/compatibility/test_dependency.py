import unittest
from scripts.measure_train.compatibility.dependency import propagate
class T(unittest.TestCase):
 def test_broken_dependency_blocks(self): self.assertEqual(propagate("PARTIAL_ALIVE",["BUILD_BROKEN"]),"BLOCKED")
