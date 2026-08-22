import unittest
from scripts.measure_train.supersession.dependency import propagate

class TestDependency(unittest.TestCase):
    def test_failure_blocks_consumer(self):
        result=propagate(["app","dep"],[("app","dep")],{"app":"PARTIAL_ALIVE","dep":"BUILD_BROKEN"})
        self.assertEqual(result["app"],"BLOCKED")
