import unittest
from scripts.edge_retirement.edge_retirement import Edge, admit, replay
S="a"*40
class Court(unittest.TestCase):
 def test_replay(self):
  e=Edge("E-REP-01",S,("machine",),"typed repair demand")
  self.assertTrue(replay(e,admit(e)))
 def test_order_duplicate_invariant(self):
  a=admit(Edge("E",S,("machine","machine"),"c"))
  b=admit(Edge("E",S,("machine",),"c"))
  self.assertEqual(a.digest,b.digest)
 def test_human_llm_not_retired(self):
  for o in (("machine","human"),("machine","llm"),("human",)):
   with self.assertRaises(ValueError): admit(Edge("E",S,o,"c"))
 def test_mutable_subject_refused(self):
  with self.assertRaises(ValueError): admit(Edge("E","main",("machine",),"c"))
 def test_consequence_changes_receipt(self):
  self.assertNotEqual(admit(Edge("E",S,("machine",),"a")).digest,admit(Edge("E",S,("machine",),"b")).digest)
if __name__=="__main__": unittest.main()
