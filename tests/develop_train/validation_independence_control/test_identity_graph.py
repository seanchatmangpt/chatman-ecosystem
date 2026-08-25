import unittest
from scripts.develop_train.validation_independence_control import Evidence, EvidenceGraph, Refused, Subject

class IdentityGraphCourt(unittest.TestCase):
    def test_exact_subject_and_acyclic_ancestry(self):
        s = Subject.parse("seanchatmangpt/chatman-ecosystem@" + "a"*40 + "#" + "b"*64)
        self.assertEqual(s.key, "seanchatmangpt/chatman-ecosystem@" + "a"*40 + "#" + "b"*64)
        graph = EvidenceGraph((
            Evidence("root", 7, (), 1),
            Evidence("left", 7, ("root",), 2),
            Evidence("right", 7, ("root",), 3),
            Evidence("leaf", 7, ("left","right"), 4),
        ))
        self.assertEqual(graph.ancestors("leaf"), frozenset({"root","left","right"}))
        self.assertLess(graph.order.index("root"), graph.order.index("leaf"))

    def test_malformed_missing_parent_and_cycle_refuse(self):
        with self.assertRaises(Refused):
            Subject.parse("owner/repo@short#" + "b"*64)
        with self.assertRaises(Refused) as missing:
            EvidenceGraph((Evidence("leaf", 1, ("ghost",), 1),))
        self.assertEqual(missing.exception.code, "MISSING_PARENT")
        with self.assertRaises(Refused) as cycle:
            EvidenceGraph((Evidence("a",1,("b",),1), Evidence("b",1,("a",),1)))
        self.assertEqual(cycle.exception.code, "EVIDENCE_CYCLE")

if __name__ == "__main__": unittest.main()
