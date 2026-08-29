import unittest
from scripts.release_train.graph import Edge, dependency_closure, is_dependency_closed, GraphRefusal

class GraphTests(unittest.TestCase):
    def test_orders_dependencies_before_root(self):
        edges=[Edge("ggen","gymact"),Edge("gymact","chatman-ecosystem")]
        self.assertEqual(dependency_closure("chatman-ecosystem",edges),("ggen","gymact","chatman-ecosystem"))
    def test_refuses_cycle(self):
        with self.assertRaisesRegex(GraphRefusal,"DEPENDENCY_CYCLE"):
            dependency_closure("a",[Edge("a","b"),Edge("b","a")])
    def test_closure_check(self):
        self.assertFalse(is_dependency_closed("b",["b"],[Edge("a","b")]))
